import { supabase } from './supabaseClient';

/**
 * Multi-Domain Assessment Service
 * Handles domain selection, adaptive question weighting, and multi-domain assessment generation
 * Supports 13 domains with adaptive difficulty based on student selections
 */

export const DOMAINS = {
  IOT: { id: 'iot', name: 'IoT', fullName: 'Internet of Things (IoT)', icon: 'Cpu', color: 'blue' },
  BLOCKCHAIN: { id: 'blockchain', name: 'Blockchain', fullName: 'Blockchain Technology', icon: 'Link', color: 'purple' },
  HUMANOID_ROBOTICS: { id: 'humanoid_robotics', name: 'Humanoid Robotics', fullName: 'Humanoid Robotics', icon: 'Bot', color: 'green' },
  AI_ML_DS: { id: 'ai_ml_ds', name: 'AI/ML/DS', fullName: 'AI/ML/Data Science', icon: 'Brain', color: 'pink' },
  DRONE_TECH: { id: 'drone_tech', name: 'Drone Tech', fullName: 'Drone Technology', icon: 'Plane', color: 'cyan' },
  BIOTECHNOLOGY: { id: 'biotechnology', name: 'Biotechnology', fullName: 'Biotechnology', icon: 'Dna', color: 'lime' },
  PHARMA_TECH: { id: 'pharma_tech', name: 'Pharma Tech', fullName: 'Pharmaceutical Technology', icon: 'Pill', color: 'rose' },
  GAMING: { id: 'gaming', name: 'Gaming', fullName: 'Gaming & Game Development', icon: 'Gamepad2', color: 'orange' },
  VR_AR: { id: 'vr_ar_immersive', name: 'VR/AR', fullName: 'VR/AR/Immersive Tech', icon: 'Glasses', color: 'violet' },
  CYBERSECURITY: { id: 'cybersecurity', name: 'CyberSecurity', fullName: 'Cybersecurity', icon: 'Shield', color: 'red' },
  WEB_DEV: { id: 'web_dev', name: 'Web Development', fullName: 'Web Development (Full-stack + AI)', icon: 'Code', color: 'yellow' },
  THREE_D_PRINTING: { id: '3d_printing', name: '3D Printing', fullName: '3D Printing / Additive Manufacturing', icon: 'Box', color: 'indigo' },
  QUANTUM: { id: 'quantum_computing', name: 'Quantum Computing', fullName: 'Quantum Computing', icon: 'Atom', color: 'fuchsia' }
};

export class MultiDomainAssessmentService {
  /**
   * Get all available domains for selection
   */
  static async getAllDomains() {
    const { data, error } = await supabase
      .from('study_fields')
      .select('*')
      .eq('is_active', true)
      .order('field_id');

    if (error) {
      console.error('Error fetching domains:', error);
      // Fallback to hardcoded domains
      return Object.values(DOMAINS);
    }

    return data || Object.values(DOMAINS);
  }

  /**
   * Get question count for each domain
   */
  static async getDomainQuestionCounts() {
    const { data, error } = await supabase
      .from('question_banks')
      .select('category')
      .eq('is_active', true);

    if (error) {
      console.error('Error fetching question counts:', error);
      return {};
    }

    const counts = {};
    data.forEach(q => {
      counts[q.category] = (counts[q.category] || 0) + 1;
    });

    return counts;
  }

  /**
   * Validate domain selection (minimum 1 domain required)
   */
  static validateDomainSelection(selectedDomains) {
    if (!selectedDomains || selectedDomains.length === 0) {
      return {
        valid: false,
        error: 'Please select at least one domain'
      };
    }

    if (selectedDomains.length > 13) {
      return {
        valid: false,
        error: 'Maximum 13 domains can be selected'
      };
    }

    return { valid: true };
  }

  /**
   * Calculate adaptive difficulty distribution based on selected domains
   * More domains = slightly easier questions to manage breadth
   * Fewer domains = more hard questions to test depth
   */
  static calculateAdaptiveDifficulty(selectedDomains, totalQuestions = 10) {
    const domainCount = selectedDomains.length;

    let difficultyDistribution = {};

    if (domainCount === 1) {
      // Single domain - test depth with more hard questions
      difficultyDistribution = {
        easy: Math.floor(totalQuestions * 0.2),    // 20%
        medium: Math.floor(totalQuestions * 0.5),  // 50%
        hard: Math.ceil(totalQuestions * 0.3)      // 30%
      };
    } else if (domainCount === 2) {
      // Two domains - balanced
      difficultyDistribution = {
        easy: Math.floor(totalQuestions * 0.3),
        medium: Math.floor(totalQuestions * 0.5),
        hard: Math.ceil(totalQuestions * 0.2)
      };
    } else if (domainCount <= 4) {
      // 3-4 domains - slightly more easy
      difficultyDistribution = {
        easy: Math.floor(totalQuestions * 0.4),
        medium: Math.floor(totalQuestions * 0.4),
        hard: Math.ceil(totalQuestions * 0.2)
      };
    } else {
      // 5+ domains - breadth over depth
      difficultyDistribution = {
        easy: Math.floor(totalQuestions * 0.5),
        medium: Math.floor(totalQuestions * 0.4),
        hard: Math.ceil(totalQuestions * 0.1)
      };
    }

    // Ensure total equals totalQuestions
    const sum = difficultyDistribution.easy + difficultyDistribution.medium + difficultyDistribution.hard;
    if (sum < totalQuestions) {
      difficultyDistribution.medium += (totalQuestions - sum);
    }

    return difficultyDistribution;
  }

  /**
   * Calculate how many questions to pull from each domain
   */
  static calculateDomainDistribution(selectedDomains, totalQuestions = 10) {
    const domainCount = selectedDomains.length;
    
    // Base questions per domain
    const basePerDomain = Math.floor(totalQuestions / domainCount);
    let remainder = totalQuestions % domainCount;

    const distribution = {};
    selectedDomains.forEach((domain, index) => {
      distribution[domain] = basePerDomain + (index < remainder ? 1 : 0);
    });

    return distribution;
  }

  /**
   * Generate multi-domain assessment
   * @param {Array} selectedDomains - Array of domain IDs
   * @param {Number} totalQuestions - Total number of questions (default: 10)
   * @param {String} userId - User ID for tracking
   */
  static async generateMultiDomainAssessment(selectedDomains, totalQuestions = 10, userId = null) {
    // Validate selection
    const validation = this.validateDomainSelection(selectedDomains);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    // Calculate adaptive difficulty
    const difficultyDist = this.calculateAdaptiveDifficulty(selectedDomains, totalQuestions);
    console.log('📊 Adaptive Difficulty Distribution:', difficultyDist);

    // Calculate domain distribution
    const domainDist = this.calculateDomainDistribution(selectedDomains, totalQuestions);
    console.log('📊 Domain Distribution:', domainDist);

    // Fetch questions for each domain
    const questions = [];
    
    for (const domainId of selectedDomains) {
      const questionsNeeded = domainDist[domainId];
      
      // Calculate difficulty split for this domain
      const domainDifficultyDist = this.calculateDifficultyForDomain(
        questionsNeeded,
        difficultyDist,
        totalQuestions
      );

      // Fetch questions from database
      const domainQuestions = await this.fetchQuestionsForDomain(
        domainId,
        domainDifficultyDist
      );

      questions.push(...domainQuestions);
    }

    // Shuffle questions to mix domains
    const shuffledQuestions = this.shuffleArray(questions);

    console.log(`✅ Generated ${shuffledQuestions.length} questions across ${selectedDomains.length} domains`);
    
    return {
      questions: shuffledQuestions.slice(0, totalQuestions),
      metadata: {
        selectedDomains,
        domainCount: selectedDomains.length,
        totalQuestions,
        difficultyDistribution: difficultyDist,
        domainDistribution: domainDist,
        adaptiveLevel: this.getAdaptiveLevel(selectedDomains.length),
        generatedAt: new Date().toISOString(),
        userId
      }
    };
  }

  /**
   * Calculate difficulty distribution for a single domain
   */
  static calculateDifficultyForDomain(questionsNeeded, overallDifficultyDist, totalQuestions) {
    const ratio = questionsNeeded / totalQuestions;
    
    return {
      easy: Math.round(overallDifficultyDist.easy * ratio),
      medium: Math.round(overallDifficultyDist.medium * ratio),
      hard: Math.round(overallDifficultyDist.hard * ratio)
    };
  }

  /**
   * Fetch questions from database for a specific domain and difficulty mix
   */
  static async fetchQuestionsForDomain(domainId, difficultyDist) {
    const questions = [];

    // Map domain IDs to category names in question_banks
    const categoryMap = {
      'iot': 'IoT',
      'blockchain': 'Blockchain',
      'humanoid_robotics': 'Humanoid Robotics',
      'ai_ml_ds': 'AI/ML/DS',
      'drone_tech': 'Drone Tech',
      'biotechnology': 'Biotechnology',
      'pharma_tech': 'Pharma Tech',
      'gaming': 'Gaming',
      'vr_ar_immersive': 'VR/AR/Immersive',
      'cybersecurity': 'CyberSecurity',
      'web_dev': 'Web Development',
      '3d_printing': '3D Printing',
      'quantum_computing': 'Quantum Computing'
    };

    const categoryName = categoryMap[domainId] || domainId;

    // Fetch for each difficulty level
    for (const [difficulty, count] of Object.entries(difficultyDist)) {
      if (count > 0) {
        const { data, error } = await supabase
          .from('question_banks')
          .select('*')
          .eq('category', categoryName)
          .eq('difficulty', difficulty)
          .eq('is_active', true)
          .limit(count);

        if (error) {
          console.error(`Error fetching ${difficulty} questions for ${domainId}:`, error);
        } else if (data && data.length > 0) {
          questions.push(...data);
        }
      }
    }

    return questions;
  }

  /**
   * Get adaptive level description
   */
  static getAdaptiveLevel(domainCount) {
    if (domainCount === 1) return 'Depth Focus (Single Domain)';
    if (domainCount === 2) return 'Balanced (2 Domains)';
    if (domainCount <= 4) return 'Multi-Disciplinary (3-4 Domains)';
    return 'Breadth Focus (5+ Domains)';
  }

  /**
   * Shuffle array (Fisher-Yates algorithm)
   */
  static shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  /**
   * Save student domain selection
   */
  static async saveStudentDomainSelection(userId, selectedDomains, assessmentId = null) {
    const { data, error } = await supabase
      .from('students')
      .update({
        background_field_of_study: selectedDomains[0], // Primary domain
        responses: {
          selected_domains: selectedDomains,
          domain_count: selectedDomains.length,
          selected_at: new Date().toISOString(),
          assessment_id: assessmentId
        },
        updated_at: new Date().toISOString()
      })
      .eq('user_id', userId);

    if (error) {
      console.error('Error saving domain selection:', error);
      throw error;
    }

    return data;
  }

  /**
   * Get student's previous domain selections
   */
  static async getStudentDomainHistory(userId) {
    const { data, error } = await supabase
      .from('students')
      .select('responses, background_field_of_study')
      .eq('user_id', userId)
      .single();

    if (error) {
      console.error('Error fetching domain history:', error);
      return null;
    }

    return {
      primaryDomain: data.background_field_of_study,
      selectedDomains: data.responses?.selected_domains || [],
      domainCount: data.responses?.domain_count || 0
    };
  }
}

export default MultiDomainAssessmentService;
