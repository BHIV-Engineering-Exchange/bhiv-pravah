// Field-based question service to replace AI generation

import { ASSIGNMENT_CONFIG, DIFFICULTY_LEVELS } from '../data/assignment.js';
import { QUESTION_BANKS, getQuestionsByCategoryAndDifficulty } from '../data/questionBanks.js';
import { STUDY_FIELDS, getQuestionWeightsForField, getDifficultyDistributionForField, detectStudyFieldFromBackground } from '../data/studyFields.js';
import { supabase } from './supabaseClient.js';
import { grokService } from './grokService.js';
import { DynamicQuestionCategoryService } from './dynamicQuestionCategoryService.js';
import { aiSettingsService } from './aiSettingsService.js';

class FieldBasedQuestionService {
  constructor() {
    this.usedQuestions = new Set();
  }

  // Resolve a category input (id or name) to { categoryId, name }
  async resolveCategory(categoryInput) {
    try {
      if (!categoryInput) return { categoryId: null, name: null };
      await DynamicQuestionCategoryService.initialize();
      let cat = await DynamicQuestionCategoryService.getCategoryById(categoryInput);
      if (cat) return { categoryId: cat.category_id, name: cat.name };
      cat = await DynamicQuestionCategoryService.getCategoryByName(categoryInput);
      if (cat) return { categoryId: cat.category_id, name: cat.name };
      const mappedId = DynamicQuestionCategoryService.mapOldCategoryToId(categoryInput);
      cat = await DynamicQuestionCategoryService.getCategoryById(mappedId);
      if (cat) return { categoryId: cat.category_id, name: cat.name };
      return { categoryId: null, name: String(categoryInput) };
    } catch (e) {
      console.warn('Category resolution failed:', e);
      return { categoryId: null, name: String(categoryInput || '') };
    }
  }

  /**
   * Generate questions based on student's study field
   * @param {Object} studentData - Student's background information
   * @param {number} totalQuestions - Total number of questions to generate
   * @returns {Promise<Array>} Array of questions
   */
  async generateQuestionsForStudent(studentData, totalQuestions = ASSIGNMENT_CONFIG.TOTAL_QUESTIONS) {
    try {
      // Detect student's study field and grade/category preferences
      const studyField = detectStudyFieldFromBackground(studentData);
      // Build education level tags for filtering (e.g., level_9..12, level_undergraduate, level_graduate, level_postgraduate)
      const levelTags = this.getStudentLevelTags(studentData);
      // Prefer explicit field from intake/background for DB mapping; fallback to detected field
      const mappingFieldId = studentData?.background_field_of_study || studentData?.responses?.field_of_study || studyField;
      console.log(`📌 Mapping field for DB queries: ${mappingFieldId} (detected: ${studyField})`);

      // A category preference could be in responses.question_category or derived elsewhere
      const preferredCategoryRaw = studentData?.responses?.question_category || null;
      const strictCategory = !!preferredCategoryRaw;

      console.log(`🎯 Detected study field: ${studyField}, levels: ${levelTags.join(',') || 'N/A'}, preferredCategory: ${preferredCategoryRaw || 'auto'}`);

      // Get weights and difficulty distribution for the field
      const questionWeights = getQuestionWeightsForField(studyField);
      const difficultyDistribution = getDifficultyDistributionForField(studyField);

      console.log(`📊 Question weights for ${studyField}:`, questionWeights);
      console.log(`📈 Difficulty distribution:`, difficultyDistribution);

      // Primary category = highest weighted category for the field, unless student picked a specific category
      const [autoPrimaryCategory] = Object.entries(questionWeights).sort((a, b) => b[1] - a[1])[0];
      const primaryCategory = preferredCategoryRaw || autoPrimaryCategory;

      // Decide high-priority admin question count: 5 for <=10 total, else up to 10
      const highPriorityCount = totalQuestions <= 10
        ? Math.min(5, totalQuestions)
        : Math.min(10, totalQuestions);

      // Helper for splitting counts by difficulty according to distribution
      const splitByDifficulty = (count) => {
        const entries = [
          [DIFFICULTY_LEVELS.EASY, difficultyDistribution.easy || 0],
          [DIFFICULTY_LEVELS.MEDIUM, difficultyDistribution.medium || 0],
          [DIFFICULTY_LEVELS.HARD, difficultyDistribution.hard || 0]
        ];
        const totals = entries.map(([, weight]) => weight);
        const weightSum = totals.reduce((a, b) => a + b, 0) || 1;
        let allocated = 0;
        const result = {};
        entries.forEach(([diff, weight], idx) => {
          let n = Math.round((weight / weightSum) * count);
          // Ensure at least 1 for the predominant difficulty when count is small
          if (count > 0 && n === 0 && idx === 1 /* medium */) n = 1;
          result[diff] = n;
          allocated += n;
        });
        // Adjust rounding errors
        const diffKeys = Object.keys(result);
        while (allocated > count) {
          for (let k of diffKeys) {
            if (allocated <= count) break;
            if (result[k] > 0) { result[k]--; allocated--; }
          }
        }
        while (allocated < count) {
          // Prefer medium then easy then hard
          for (let k of [DIFFICULTY_LEVELS.MEDIUM, DIFFICULTY_LEVELS.EASY, DIFFICULTY_LEVELS.HARD]) {
            if (allocated >= count) break;
            result[k] = (result[k] || 0) + 1; allocated++;
          }
        }
        return result;
      };

      // Check if AI question generation is enabled globally
      const isAIEnabled = await aiSettingsService.isAIEnabled();
      console.log(`🤖 AI question generation is ${isAIEnabled ? 'enabled' : 'disabled'} globally`);

      // 1) Fetch admin-managed questions mapped to the detected field, as highest priority
      const adminQuestions = [];

      // When AI is disabled, get all available admin questions regardless of difficulty distribution
      if (!isAIEnabled) {
        console.log(`🤖 AI disabled, fetching all available admin questions for category: ${primaryCategory}`);
        
        // Get all admin questions for the category, trying all difficulties
        const allDifficulties = [DIFFICULTY_LEVELS.EASY, DIFFICULTY_LEVELS.MEDIUM, DIFFICULTY_LEVELS.HARD];
        let totalFetched = 0;
        
        for (const difficulty of allDifficulties) {
          if (totalFetched >= totalQuestions) break;
          
          const remainingNeeded = totalQuestions - totalFetched;
          
          // Prefer field-mapped questions with grade filter
          let dbQs = await this.getFieldMappedQuestionsFromDatabase(mappingFieldId, primaryCategory, difficulty, remainingNeeded, levelTags, true);
          // If not enough, fallback to category-only admin questions filtered by education level
          if (dbQs.length < remainingNeeded) {
            const topUp = await this.getQuestionsFromDatabase(primaryCategory, difficulty, remainingNeeded - dbQs.length, levelTags, true);
            dbQs = dbQs.concat(topUp);
          }
          
          // Map to expected structure with metadata
          dbQs.forEach(q => adminQuestions.push({
            ...q,
            category: primaryCategory,
            difficulty: q.difficulty || difficulty, // Use actual difficulty from DB
            type: 'multiple_choice',
            points: q.points ?? 10,
            time_limit_seconds: q.time_limit_seconds ?? 180
          }));
          
          totalFetched += dbQs.length;
        }
      } else {
        // AI is enabled, use difficulty distribution for admin questions
        const adminCounts = splitByDifficulty(highPriorityCount);

        for (const [difficulty, count] of Object.entries(adminCounts)) {
          if (count <= 0) continue;
          // Prefer field-mapped questions with grade filter
          let dbQs = await this.getFieldMappedQuestionsFromDatabase(mappingFieldId, primaryCategory, difficulty, count, levelTags, true);
          // If not enough, fallback to category-only admin questions filtered by education level
          if (dbQs.length < count) {
            const topUp = await this.getQuestionsFromDatabase(primaryCategory, difficulty, count - dbQs.length, levelTags, true);
            dbQs = dbQs.concat(topUp);
          }
          // Map to expected structure with metadata
          dbQs.forEach(q => adminQuestions.push({
            ...q,
            category: primaryCategory,
            difficulty: q.difficulty || difficulty, // Use actual difficulty from DB
            type: 'multiple_choice',
            points: q.points ?? 10,
            time_limit_seconds: q.time_limit_seconds ?? 180
          }));
        }
      }

      // 2) Generate remaining with AI only if enabled, otherwise use admin questions
      const remainingCount = Math.max(0, totalQuestions - adminQuestions.length);
      const aiQuestions = [];

      if (isAIEnabled && remainingCount > 0) {
        // Build Set of normalized question texts to prevent duplicates
        const normalizeText = (t) => (t || '')
          .toLowerCase()
          .replace(/[^\w\s]/g, '')
          .replace(/\s+/g, ' ')
          .trim();
        const usedQuestionTexts = new Set(adminQuestions.map(q => normalizeText(q.question_text)));

        const aiCounts = splitByDifficulty(remainingCount);

        for (const [difficulty, count] of Object.entries(aiCounts)) {
          if (count <= 0) continue;
          try {
            const aiCategoryLabel = `${primaryCategory} | field:${mappingFieldId} | level:${(levelTags||[]).join(',') || 'any'}`;
            const aiQsRaw = await grokService.generateUniqueQuestions(
              aiCategoryLabel,
              difficulty,
              count,
              usedQuestionTexts
            );
            // Remap AI questions' category back to the selected category for consistent storage/display
            const aiQs = aiQsRaw.map(q => ({ ...q, category: primaryCategory }));
            // Persist AI-generated questions for admin visibility and future reuse
            await this.storeGeneratedQuestions(aiQs, mappingFieldId, primaryCategory, difficulty);

            aiQs.forEach(q => usedQuestionTexts.add(normalizeText(q.question_text)));
            aiQuestions.push(...aiQs);
          } catch (e) {
            console.warn(`⚠️ Grok generation failed for ${primaryCategory} - ${difficulty}: ${e.message}. Falling back to curated bank.`);
            // Fallback to curated question bank if AI fails
            const fallback = await this.getQuestionsForCategoryAndDifficulty(primaryCategory, difficulty, count);
            fallback.forEach(q => usedQuestionTexts.add(normalizeText(q.question_text)));
            aiQuestions.push(...fallback);
          }
        }
      } else if (remainingCount > 0) {
        // AI is disabled, fill remaining with admin questions from any difficulty
        console.log(`🤖 AI disabled, filling remaining ${remainingCount} questions with admin questions from any difficulty`);
        const normalizeText = (t) => (t || '')
          .toLowerCase()
          .replace(/[^\w\s]/g, '')
          .replace(/\s+/g, ' ')
          .trim();
        const usedQuestionTexts = new Set(adminQuestions.map(q => normalizeText(q.question_text)));
        
        // When AI is disabled, get admin questions from any difficulty to ensure we have questions
        const allDifficulties = [DIFFICULTY_LEVELS.EASY, DIFFICULTY_LEVELS.MEDIUM, DIFFICULTY_LEVELS.HARD];
        let remainingNeeded = remainingCount;
        
        for (const difficulty of allDifficulties) {
          if (remainingNeeded <= 0) break;
          
          try {
            const adminQs = await this.getQuestionsFromDatabase(primaryCategory, difficulty, remainingNeeded, levelTags, true);
            // Filter out duplicates
            const uniqueAdminQs = adminQs.filter(q => {
              const normalizedText = normalizeText(q.question_text);
              if (usedQuestionTexts.has(normalizedText)) {
                return false;
              }
              usedQuestionTexts.add(normalizedText);
              return true;
            });
            
            // Map to expected structure with metadata
            uniqueAdminQs.forEach(q => aiQuestions.push({
              ...q,
              category: primaryCategory,
              difficulty: q.difficulty || difficulty, // Use actual difficulty from DB
              type: 'multiple_choice',
              points: q.points ?? 10,
              time_limit_seconds: q.time_limit_seconds ?? 180
            }));
            
            remainingNeeded -= uniqueAdminQs.length;
          } catch (e) {
            console.warn(`⚠️ Failed to fetch admin questions for ${primaryCategory} - ${difficulty}: ${e.message}`);
          }
        }
      }

      // Combine: admin high-priority first, then AI-generated or additional admin
      let combined = [...adminQuestions, ...aiQuestions];

      // Top-up strictly from DB with same constraints (category + optional grade)
      if (combined.length < totalQuestions) {
        const usedTexts = new Set(combined.map(q => (q.question_text || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim()));
        const fillOrder = [DIFFICULTY_LEVELS.MEDIUM, DIFFICULTY_LEVELS.EASY, DIFFICULTY_LEVELS.HARD];
        for (const diff of fillOrder) {
          if (combined.length >= totalQuestions) break;
          const remaining = totalQuestions - combined.length;
          const pool = await this.getQuestionsFromDatabase(primaryCategory, diff, remaining * 2, levelTags, true);
          const unique = pool.filter(q => !usedTexts.has((q.question_text || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim()));
          const picked = this.selectRandomQuestions(unique.length ? unique : pool, remaining).map(q => ({
            ...q,
            category: primaryCategory,
            difficulty: diff,
            type: 'multiple_choice',
            points: q.points ?? 10,
            time_limit_seconds: q.time_limit_seconds ?? 180
          }));
          picked.forEach(p => usedTexts.add((p.question_text || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim()));
          combined = combined.concat(picked);
        }
      }

      // If strict category chosen and still short, and AI is enabled, top-up with AI
      if (strictCategory && isAIEnabled && combined.length < totalQuestions) {
        const remaining = totalQuestions - combined.length;
        const usedTexts = new Set(combined.map(q => (q.question_text || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim()));
        const aiCounts = splitByDifficulty(remaining);
        for (const [diff, cnt] of Object.entries(aiCounts)) {
          if (cnt <= 0) continue;
          try {
            const aiLabel = `${primaryCategory} | field:${mappingFieldId} | level:${(levelTags||[]).join(',') || 'any'}`;
            const aiQsRaw = await grokService.generateUniqueQuestions(aiLabel, diff, cnt, usedTexts);
            const aiQs = aiQsRaw.map(q => ({ ...q, category: primaryCategory }));
            await this.storeGeneratedQuestions(aiQs, mappingFieldId, primaryCategory, diff);
            aiQs.forEach(q => usedTexts.add((q.question_text || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim()));
            combined.push(...aiQs);
          } catch (e) {
            console.warn(`⚠️ Forced AI generation failed for ${primaryCategory} - ${diff}: ${e.message}`);
          }
        }
      }

      // Curated bank fallback only when AI is enabled and category is not strict
      if (!strictCategory && isAIEnabled && combined.length < totalQuestions) {
        const remaining = totalQuestions - combined.length;
        const curatedCounts = splitByDifficulty(remaining);
        for (const [diff, count] of Object.entries(curatedCounts)) {
          if (count <= 0) continue;
          try {
            const fromBank = await this.getQuestionsForCategoryAndDifficulty(primaryCategory, diff, count);
            combined.push(...fromBank);
            if (combined.length >= totalQuestions) break;
          } catch (e) {
            console.warn(`⚠️ Curated bank fallback failed for ${primaryCategory} - ${diff}: ${e.message}`);
          }
        }
      }

      // If still not enough and AI is enabled, broaden to other categories based on field weights
      if (!strictCategory && isAIEnabled && combined.length < totalQuestions) {
        const remainingNeeded = totalQuestions - combined.length;
        const categoriesByWeight = Object.entries(questionWeights)
          .sort((a, b) => b[1] - a[1])
          .map(([c]) => c);
        const fillOrder = [DIFFICULTY_LEVELS.MEDIUM, DIFFICULTY_LEVELS.EASY, DIFFICULTY_LEVELS.HARD];
        const existingNormTexts = new Set(
          combined.map(q => (q.question_text || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim())
        );
        let added = 0;
        for (const diff of fillOrder) {
          if (added >= remainingNeeded) break;
          for (const cat of categoriesByWeight) {
            if (added >= remainingNeeded) break;
            try {
              const batch = await this.getQuestionsForCategoryAndDifficulty(cat, diff, (remainingNeeded - added));
              for (const q of batch) {
                const norm = (q.question_text || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
                if (existingNormTexts.has(norm)) continue;
                combined.push(q);
                existingNormTexts.add(norm);
                added++;
                if (added >= remainingNeeded) break;
              }
            } catch (e) {
              console.warn(`⚠️ Expanded curated fallback failed for ${cat} - ${diff}: ${e.message}`);
            }
          }
        }
      }

      combined = combined.slice(0, totalQuestions);

      console.log(`✅ Generated blended set: ${combined.length} questions (admin: ${adminQuestions.length}, ai: ${aiQuestions.length}) for field ${studyField} [primary: ${primaryCategory}]`);
      return combined;

    } catch (error) {
      console.error('❌ Error generating field-based questions:', error);
      // Fallback to previous distribution-based method
      try {
        const questionWeights = getQuestionWeightsForField(detectStudyFieldFromBackground(studentData));
        const difficultyDistribution = getDifficultyDistributionForField(detectStudyFieldFromBackground(studentData));
        const questionDistribution = this.calculateQuestionDistribution(
          questionWeights,
          difficultyDistribution,
          totalQuestions
        );
        const questions = await this.generateQuestionsFromDistribution(questionDistribution);
        console.warn('↩️ Falling back to distribution-based questions.');
        return questions;
      } catch {
        throw new Error(`Failed to generate questions: ${error.message}`);
      }
    }
  }

  /**
   * Calculate question distribution based on weights and difficulty
   */
  calculateQuestionDistribution(questionWeights, difficultyDistribution, totalQuestions) {
    const distribution = {};

    // Calculate questions per category based on weights
    Object.entries(questionWeights).forEach(([category, weight]) => {
      const questionsForCategory = Math.round((weight / 100) * totalQuestions);
      if (questionsForCategory > 0) {
        distribution[category] = {
          total: questionsForCategory,
          difficulties: {}
        };

        // Distribute across difficulties
        Object.entries(difficultyDistribution).forEach(([difficulty, diffWeight]) => {
          const questionsForDifficulty = Math.round((diffWeight / 100) * questionsForCategory);
          if (questionsForDifficulty > 0) {
            distribution[category].difficulties[difficulty] = questionsForDifficulty;
          }
        });
      }
    });

    // Ensure we have exactly the right number of questions
    this.adjustDistributionToTotal(distribution, totalQuestions);

    return distribution;
  }

  /**
   * Adjust distribution to match exact total
   */
  adjustDistributionToTotal(distribution, totalQuestions) {
    let currentTotal = 0;
    
    // Count current total
    Object.values(distribution).forEach(categoryDist => {
      Object.values(categoryDist.difficulties).forEach(count => {
        currentTotal += count;
      });
    });

    // Adjust if needed
    const difference = totalQuestions - currentTotal;
    if (difference !== 0) {
      // Find the category with the highest weight to adjust
      const categories = Object.keys(distribution);
      if (categories.length > 0) {
        const mainCategory = categories[0]; // Assume first category has highest weight
        const difficulties = Object.keys(distribution[mainCategory].difficulties);
        if (difficulties.length > 0) {
          const mainDifficulty = difficulties[0];
          distribution[mainCategory].difficulties[mainDifficulty] += difference;
          
          // Ensure no negative values
          if (distribution[mainCategory].difficulties[mainDifficulty] < 0) {
            distribution[mainCategory].difficulties[mainDifficulty] = 1;
          }
        }
      }
    }
  }

  /**
   * Generate questions from calculated distribution
   */
  async generateQuestionsFromDistribution(distribution) {
    const questions = [];
    this.usedQuestions.clear();

    for (const [category, categoryDist] of Object.entries(distribution)) {
      for (const [difficulty, count] of Object.entries(categoryDist.difficulties)) {
        if (count > 0) {
          const categoryQuestions = await this.getQuestionsForCategoryAndDifficulty(
            category,
            difficulty,
            count
          );
          questions.push(...categoryQuestions);
        }
      }
    }

    // Shuffle questions to randomize order
    return this.shuffleArray(questions);
  }

  /**
   * Get questions for specific category and difficulty
   */
  async getQuestionsForCategoryAndDifficulty(category, difficulty, count) {
    const availableQuestions = getQuestionsByCategoryAndDifficulty(category, difficulty);
    
    if (availableQuestions.length === 0) {
      console.warn(`⚠️ No questions available for ${category} - ${difficulty}`);
      return [];
    }

    // Filter out already used questions
    const unusedQuestions = availableQuestions.filter(q => !this.usedQuestions.has(q.id));
    
    if (unusedQuestions.length === 0) {
      console.warn(`⚠️ All questions for ${category} - ${difficulty} have been used`);
      // If all questions used, reset and use available questions
      return this.selectRandomQuestions(availableQuestions, count);
    }

    const selectedQuestions = this.selectRandomQuestions(unusedQuestions, count);
    
    // Mark questions as used
    selectedQuestions.forEach(q => this.usedQuestions.add(q.id));

    // Add metadata
    return selectedQuestions.map(question => ({
      ...question,
      category,
      difficulty,
      type: 'multiple_choice',
      points: 10,
      time_limit_seconds: 180
    }));
  }

  /**
   * Select random questions from array
   */
  selectRandomQuestions(questions, count) {
    const shuffled = this.shuffleArray([...questions]);
    return shuffled.slice(0, Math.min(count, shuffled.length));
  }

  /**
   * Shuffle array using Fisher-Yates algorithm
   */
  shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  /**
   * Get questions from database (for admin-managed questions) - WITH ENHANCED DEBUGGING
   */
  async getQuestionsFromDatabase(category, difficulty, count, levelTags = [], excludeAI = false) {
    try {
      console.log(`🔍 Fetching general questions: category=${category}, difficulty=${difficulty}, count=${count}, levelTags=${(levelTags||[]).join(',') || 'any'}, excludeAI=${excludeAI}`);
      
      // Start with basic filters
      let query = supabase
        .from('question_banks')
        .select('*')
        .eq('is_active', true);

      if (excludeAI) {
        query = query.eq('created_by', 'admin');
      }

      // Apply category filter - try both category_id and category name
      const { categoryId, name: categoryName } = await this.resolveCategory(category);
      console.log(`🏷️ Category resolution: input="${category}" -> categoryId="${categoryId}", name="${categoryName}"`);
      
      if (categoryId) {
        query = query.eq('category_id', categoryId);
      } else {
        // Use ilike for case-insensitive category matching
        query = query.ilike('category', categoryName || category);
      }

      // Apply difficulty filter with case-insensitive matching
      query = query.ilike('difficulty', difficulty);

      // Apply education level filtering if provided
      if (Array.isArray(levelTags) && levelTags.length > 0) {
        query = query.overlaps('tags', levelTags);
      }

      query = query.limit(count * 3);

      const { data, error } = await query;

      if (error) {
        console.error('❌ Error fetching questions from database:', error);
        return [];
      }

      console.log(`✅ Initial query returned ${data?.length || 0} questions`);
      if (data && data.length > 0) {
        console.log(`📋 Sample question:`, {
          question_id: data[0].question_id,
          category: data[0].category,
          category_id: data[0].category_id,
          difficulty: data[0].difficulty,
          created_by: data[0].created_by,
          tags: data[0].tags
        });
      }

      let pool = data || [];

      // If not enough and level filter was applied, try without level as fallback
      if (pool.length < count && Array.isArray(levelTags) && levelTags.length > 0) {
        console.log(`🔄 Retrying without level tags filter...`);
        let noLevelQuery = supabase
          .from('question_banks')
          .select('*')
          .eq('is_active', true)
          .ilike('difficulty', difficulty)
          .limit(count * 2);
          
        if (excludeAI) {
          noLevelQuery = noLevelQuery.eq('created_by', 'admin');
        }
        
        if (categoryId) {
          noLevelQuery = noLevelQuery.eq('category_id', categoryId);
        } else {
          noLevelQuery = noLevelQuery.ilike('category', categoryName || category);
        }
        
        const { data: noLevelData, error: noLevelErr } = await noLevelQuery;
        if (!noLevelErr && noLevelData) {
          console.log(`✅ No-level query returned ${noLevelData.length} additional questions`);
          const ids = new Set(pool.map(q => q.question_id));
          noLevelData.forEach(q => { if (!ids.has(q.question_id)) pool.push(q); });
        }
      }

      // Final fallback: ignore difficulty, keep category only
      if (pool.length < count) {
        console.log(`🔄 Final fallback: ignoring difficulty, category-only search...`);
        let catOnlyQuery = supabase
          .from('question_banks')
          .select('*')
          .eq('is_active', true)
          .limit(count * 3);
          
        if (excludeAI) {
          catOnlyQuery = catOnlyQuery.eq('created_by', 'admin');
        }
        
        if (categoryId) {
          catOnlyQuery = catOnlyQuery.eq('category_id', categoryId);
        } else {
          catOnlyQuery = catOnlyQuery.ilike('category', categoryName || category);
        }
        
        // In admin-only mode (excludeAI), do not restrict by level tags on final category-only fallback
        if (!excludeAI && Array.isArray(levelTags) && levelTags.length > 0) {
          catOnlyQuery = catOnlyQuery.overlaps('tags', levelTags);
        }
        
        const { data: catOnlyData, error: catOnlyErr } = await catOnlyQuery;
        if (!catOnlyErr && catOnlyData) {
          console.log(`✅ Category-only query returned ${catOnlyData.length} additional questions`);
          const ids2 = new Set(pool.map(q => q.question_id));
          catOnlyData.forEach(q => { if (!ids2.has(q.question_id)) pool.push(q); });
        } else if (catOnlyErr) {
          console.error('❌ Category-only query error:', catOnlyErr);
        }
      }

      console.log(`📊 Final pool size: ${pool.length} questions`);
      return this.selectRandomQuestions(pool, count);
    } catch (error) {
      console.error('❌ Database query error:', error);
      return [];
    }
  }

  /**
   * Get questions mapped to a study field via question_field_mapping
   */
  async getFieldMappedQuestionsFromDatabase(fieldId, category, difficulty, count, levelTags = [], excludeAI = false) {
    try {
      console.log(`🔍 Fetching field-mapped questions for field: ${fieldId}, category: ${category}, difficulty: ${difficulty}, count=${count}, levelTags=${(levelTags||[]).join(',') || 'any'}`);
      
      // 1) Find question_ids mapped to the field
      const { data: mappings, error: mapErr } = await supabase
        .from('question_field_mapping')
        .select('question_id')
        .eq('field_id', fieldId);

      if (mapErr) {
        console.warn('Mapping fetch error:', mapErr);
        return [];
      }

      const ids = (mappings || []).map(m => m.question_id);
      if (!ids.length) {
        console.log(`❌ No questions mapped to field ${fieldId}`);
        return [];
      }

      // 2) Pull questions by ids with filters
      let query = supabase
        .from('question_banks')
        .select('*')
        .in('question_id', ids)
        .ilike('difficulty', difficulty)
        .eq('is_active', true);

      if (excludeAI) {
        query = query.eq('created_by', 'admin');
      }

      // Apply category filter (category_id preferred, fallback to legacy name)
      try {
        const { categoryId, name: categoryName } = await this.resolveCategory(category);
        if (categoryId) {
          query = query.eq('category_id', categoryId);
        } else {
          query = query.eq('category', categoryName || category);
        }
      } catch {}

      if (Array.isArray(levelTags) && levelTags.length > 0) {
        query = query.overlaps('tags', levelTags);
      }

      query = query.limit(count * 3);
      const { data, error } = await query;

      if (error) {
        console.error('Error fetching mapped questions:', error);
        return [];
      }

      let pool = data || [];
      // If not enough and level filter applied, try without level
      if (pool.length < count && Array.isArray(levelTags) && levelTags.length > 0) {
        const r = await this.resolveCategory(category);
        let noLevelQuery = supabase
          .from('question_banks')
          .select('*')
          .in('question_id', ids)
          .ilike('difficulty', difficulty)
          .eq('is_active', true)
          .limit(count * 2);
        if (excludeAI) {
          noLevelQuery = noLevelQuery.eq('created_by', 'admin');
        }
        noLevelQuery = r.categoryId
          ? noLevelQuery.eq('category_id', r.categoryId)
          : noLevelQuery.eq('category', r.name || category);
        const { data: noLevelData, error: noLevelErr } = await noLevelQuery;
        if (!noLevelErr && noLevelData) {
          const idset = new Set(pool.map(q => q.question_id));
          noLevelData.forEach(q => { if (!idset.has(q.question_id)) pool.push(q); });
        }
      }
      // Final fallback: ignore difficulty, keep category only (still restricted to mapped ids)
      if (pool.length < count) {
        const r2 = await this.resolveCategory(category);
        let catOnlyQuery = supabase
          .from('question_banks')
          .select('*')
          .in('question_id', ids)
          .eq('is_active', true)
          .limit(count * 3);
        if (excludeAI) {
          catOnlyQuery = catOnlyQuery.eq('created_by', 'admin');
        }
        catOnlyQuery = r2.categoryId
          ? catOnlyQuery.eq('category_id', r2.categoryId)
          : catOnlyQuery.eq('category', r2.name || category);
        // In admin-only mode (excludeAI), do not restrict by level tags on final category-only fallback
        if (!excludeAI && Array.isArray(levelTags) && levelTags.length > 0) {
          catOnlyQuery = catOnlyQuery.overlaps('tags', levelTags);
        }
        const { data: catOnlyData, error: catOnlyErr } = await catOnlyQuery;
        if (!catOnlyErr && catOnlyData) {
          const ids2 = new Set(pool.map(q => q.question_id));
          catOnlyData.forEach(q => { if (!ids2.has(q.question_id)) pool.push(q); });
        }
      }

      console.log(`✅ Successfully fetched ${pool.length} field-mapped questions for ${fieldId}`);
      return this.selectRandomQuestions(pool, count);
    } catch (error) {
      console.error('Database query error (mapped):', error);
      return [];
    }
  }

  /**
   * Update question usage statistics
   */
  async updateQuestionStats(questionId, isCorrect, timeSeconds) {
    try {
      const { error } = await supabase.rpc('update_question_usage_stats', {
        p_question_id: questionId,
        p_is_correct: isCorrect,
        p_time_seconds: timeSeconds
      });

      if (error) {
        console.error('Error updating question stats:', error);
      }
    } catch (error) {
      console.error('Error updating question statistics:', error);
    }
  }

  // Persist AI-generated questions into Supabase and map them to a study field for admin visibility
  async storeGeneratedQuestions(generatedQuestions, fieldId, category, difficulty) {
    try {
      if (!Array.isArray(generatedQuestions) || generatedQuestions.length === 0) return;

      // Prepare upsert payload for question_banks
      const nowIso = new Date().toISOString();
      const { categoryId: resolvedCategoryId, name: resolvedCategoryName } = await this.resolveCategory(category);
      const payload = generatedQuestions.map((q) => {
        // Derive a deterministic question_id from text + category + difficulty
        const base = `${(q.question_text || '').toLowerCase()}|${resolvedCategoryName || category}|${difficulty}`;
        let hash = 0;
        for (let i = 0; i < base.length; i++) {
          hash = ((hash << 5) - hash) + base.charCodeAt(i);
          hash |= 0;
        }
        const question_id = `AI_${(resolvedCategoryName || category)}_${difficulty}_${Math.abs(hash)}`;
        return {
          question_id,
          category: resolvedCategoryName || category,
          category_id: resolvedCategoryId || null,
          difficulty,
          question_text: q.question_text,
          options: q.options,
          correct_answer: q.correct_answer,
          explanation: q.explanation || '',
          vedic_connection: q.vedic_connection || '',
          modern_application: q.modern_application || '',
          tags: ['ai_generated'],
          is_active: true,
          created_by: 'ai',
          created_at: nowIso,
          updated_at: nowIso
        };
      });

      // Upsert into question_banks
      const { error } = await supabase
        .from('question_banks')
        .upsert(payload, { onConflict: 'question_id' });

      if (error) {
        console.warn('Failed to upsert AI-generated questions:', error);
      } else {
        // Map questions to field if provided
        if (fieldId) {
          const mappings = payload.map(p => ({
            question_id: p.question_id,
            field_id: fieldId,
            weight: 1,
            is_primary: true
          }));
          
          // Try upsert first, fallback to individual inserts if constraint doesn't exist
          const { error: mapErr } = await supabase
            .from('question_field_mapping')
            .upsert(mappings, { onConflict: 'question_id,field_id' });

          if (mapErr && mapErr.code === '42P10') {
            // Constraint doesn't exist, try individual inserts with conflict handling
            console.log('Unique constraint not found, trying individual inserts...');
            for (const mapping of mappings) {
              try {
                // Check if mapping already exists
                const { data: existing } = await supabase
                  .from('question_field_mapping')
                  .select('id')
                  .eq('question_id', mapping.question_id)
                  .eq('field_id', mapping.field_id)
                  .single();

                if (!existing) {
                  // Insert only if it doesn't exist
                  const { error: insertErr } = await supabase
                    .from('question_field_mapping')
                    .insert([mapping]);
                  
                  if (insertErr) {
                    console.warn('Failed to insert question field mapping:', insertErr);
                  }
                }
              } catch (err) {
                console.warn('Error handling question field mapping:', err);
              }
            }
          } else if (mapErr) {
            console.warn('Failed to upsert AI question field mappings:', mapErr);
          }
        }
      }
    } catch (err) {
      console.warn('Error storing AI-generated questions:', err);
    }
  }

  /**
   * Get available categories and their question counts
   */
  async getQuestionBankSummary() {
    const summary = {};
    
    Object.entries(QUESTION_BANKS).forEach(([category, difficulties]) => {
      summary[category] = {};
      Object.entries(difficulties).forEach(([difficulty, questions]) => {
        summary[category][difficulty] = questions.length;
      });
    });

    return summary;
  }

  /**
   * Search questions by text
   */
  searchQuestions(searchTerm) {
    const results = [];
    
    Object.entries(QUESTION_BANKS).forEach(([category, difficulties]) => {
      Object.entries(difficulties).forEach(([difficulty, questions]) => {
        questions.forEach(question => {
          if (
            question.question_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
            question.explanation.toLowerCase().includes(searchTerm.toLowerCase())
          ) {
            results.push({
              ...question,
              category,
              difficulty
            });
          }
        });
      });
    });

    return results;
  }

  /**
   * Validate question format
   */
  validateQuestion(question) {
    const required = ['question_text', 'options', 'correct_answer', 'explanation'];
    const missing = required.filter(field => !question[field]);
    
    if (missing.length > 0) {
      throw new Error(`Missing required fields: ${missing.join(', ')}`);
    }

    if (!Array.isArray(question.options) || question.options.length !== 4) {
      throw new Error('Questions must have exactly 4 options');
    }

    if (!question.options.includes(question.correct_answer)) {
      throw new Error('Correct answer must be one of the provided options');
    }

    return true;
  }

  /**
   * Derive education level tag(s) from student data
   * Returns array of tags to match, e.g., ['level_9','grade_9'] or ['level_undergraduate']
   */
  getStudentLevelTags(studentData) {
    const tags = [];

    // Try to find an explicit numeric grade (9-12)
    const gradeRaw = studentData?.grade || studentData?.responses?.grade || '';
    const numeric = String(gradeRaw).match(/\b(9|10|11|12)\b/);
    if (numeric) {
      const g = numeric[1];
      tags.push(`level_${g}`, `grade_${g}`); // include legacy grade_ tag for compatibility
      return tags;
    }

    // Try to use class_level/education level
    const lvl = studentData?.responses?.class_level || studentData?.class_level || studentData?.background_class_level || '';
    switch ((lvl || '').toLowerCase()) {
      case 'high_school':
        // Unknown specific grade: accept any HS level
        tags.push('level_9', 'level_10', 'level_11', 'level_12', 'grade_9', 'grade_10', 'grade_11', 'grade_12');
        break;
      case 'undergraduate':
        tags.push('level_undergraduate');
        break;
      case 'graduate':
        tags.push('level_graduate');
        break;
      case 'postgraduate':
        tags.push('level_postgraduate');
        break;
      default:
        // No level filter
        break;
    }
    return tags;
  }
}

// Export singleton instance
export const fieldBasedQuestionService = new FieldBasedQuestionService();
export default fieldBasedQuestionService;