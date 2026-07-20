const Levenshtein = require('levenshtein');

/**
 * PART A: BIOMETRIC → EMPLOYEE MAPPING MODULE
 * 
 * Applies multi-level matching rules to resolve ambiguous biometric identities
 * - Direct ID match
 * - Name normalization
 * - First name matching
 * - Surname initial matching
 * - Fuzzy Levenshtein distance
 */

class BiometricIdentityResolver {
  constructor() {
    this.fuzzyThreshold = 0.8; // 80% similarity threshold
    this.debug = true;
  }

  /**
   * Main function: mapBiometricToEmployee
   * 
   * @param {String} bio_id - Biometric device ID (emp_code)
   * @param {String} bio_name - Biometric name from device
   * @param {Array} employee_list - List of employee objects with { _id, firstName, lastName, biometric_code }
   * 
   * @returns {Object} { employeeId, matchType, matchData, warnings }
   */
  async mapBiometricToEmployee(bio_id, bio_name, employee_list) {
    if (!employee_list || employee_list.length === 0) {
      return {
        success: false,
        error: 'Biometric ID not found',
        errorCode: 'EMPTY_EMPLOYEE_LIST'
      };
    }

    // Rule 1: DIRECT ID MATCH
    const directMatch = this._ruleDirectIdMatch(bio_id, employee_list);
    if (directMatch) {
      this._log(`✅ Rule 1 PASSED: Direct ID match for "${bio_id}"`);
      return {
        success: true,
        employeeId: directMatch._id,
        matchType: 'DIRECT_ID_MATCH',
        matchData: directMatch,
        confidence: 1.0
      };
    }

    this._log(`❌ Rule 1 FAILED: No direct ID match for "${bio_id}"`);

    // Rule 2: NAME NORMALIZATION
    const normalizedBio = this._normalizeName(bio_name);
    this._log(`📝 Normalized biometric name: "${bio_name}" → first="${normalizedBio.first}", last="${normalizedBio.last}"`);

    // Rule 3: FIRST NAME EXACT MATCH (case-insensitive)
    const firstNameMatches = this._ruleFirstNameExactMatch(
      normalizedBio.first,
      employee_list
    );

    if (firstNameMatches.length === 1) {
      this._log(`✅ Rule 3 PASSED: Single exact first name match`);
      return {
        success: true,
        employeeId: firstNameMatches[0]._id,
        matchType: 'FIRST_NAME_EXACT',
        matchData: firstNameMatches[0],
        confidence: 0.9
      };
    }

    if (firstNameMatches.length > 1) {
      this._log(`⚠️  Rule 3 PARTIAL: Found ${firstNameMatches.length} employees with same first name`);

      // Rule 4: FIRST NAME + SURNAME INITIAL MATCH
      const surnameInitialMatches = this._ruleSurnameInitialMatch(
        normalizedBio,
        firstNameMatches
      );

      if (surnameInitialMatches.length === 1) {
        this._log(`✅ Rule 4 PASSED: Surname initial match`);
        return {
          success: true,
          employeeId: surnameInitialMatches[0]._id,
          matchType: 'FIRST_NAME_SURNAME_INITIAL',
          matchData: surnameInitialMatches[0],
          confidence: 0.85
        };
      }

      if (surnameInitialMatches.length > 1) {
        this._log(`⚠️  Rule 4 PARTIAL: Found ${surnameInitialMatches.length} matches with same surname initial`);

        // Rule 5: FIRST NAME + LAST NAME PREFIX MATCH
        const prefixMatches = this._ruleLastNamePrefixMatch(
          normalizedBio,
          surnameInitialMatches
        );

        if (prefixMatches.length === 1) {
          this._log(`✅ Rule 5 PASSED: Last name prefix match`);
          return {
            success: true,
            employeeId: prefixMatches[0]._id,
            matchType: 'FIRST_NAME_LAST_NAME_PREFIX',
            matchData: prefixMatches[0],
            confidence: 0.8
          };
        }

        if (prefixMatches.length > 1) {
          this._log(`❌ Rule 5 AMBIGUOUS: Multiple matches with same prefix`);
          return {
            success: false,
            error: 'Ambiguous match — multiple employees',
            errorCode: 'AMBIGUOUS_MATCH',
            candidates: prefixMatches.map(e => ({
              _id: e._id,
              name: `${e.firstName} ${e.lastName || ''}`,
              biometricCode: e.biometric_code
            })),
            confidence: 0.7
          };
        }
      }
    }

    // Rule 6: FUZZY MATCH (Levenshtein distance)
    const fuzzyMatches = this._ruleFuzzyMatch(bio_name, employee_list);

    if (fuzzyMatches.length === 1) {
      this._log(`✅ Rule 6 PASSED: Fuzzy match with ${fuzzyMatches[0].similarity.toFixed(2)} similarity`);
      return {
        success: true,
        employeeId: fuzzyMatches[0].employee._id,
        matchType: 'FUZZY_MATCH',
        matchData: fuzzyMatches[0].employee,
        confidence: fuzzyMatches[0].similarity,
        remarks: `Fuzzy match: "${bio_name}" ↔️ "${fuzzyMatches[0].employee.firstName} ${fuzzyMatches[0].employee.lastName}"`
      };
    }

    if (fuzzyMatches.length > 1) {
      this._log(`⚠️  Rule 6 PARTIAL: Found ${fuzzyMatches.length} fuzzy matches`);
      
      // Pick best match if similarity difference is significant
      if (fuzzyMatches[0].similarity - fuzzyMatches[1].similarity > 0.15) {
        this._log(`✅ Using best fuzzy match (significantly higher similarity)`);
        return {
          success: true,
          employeeId: fuzzyMatches[0].employee._id,
          matchType: 'FUZZY_MATCH_BEST',
          matchData: fuzzyMatches[0].employee,
          confidence: fuzzyMatches[0].similarity,
          remarks: `Fuzzy match: "${bio_name}" ↔️ "${fuzzyMatches[0].employee.firstName} ${fuzzyMatches[0].employee.lastName}"`
        };
      }
    }

    // No match found
    this._log(`❌ ALL RULES FAILED: Cannot map biometric "${bio_name}" (ID: ${bio_id})`);
    return {
      success: false,
      error: 'No matching employee found',
      errorCode: 'NO_MATCH_FOUND',
      biometricId: bio_id,
      biometricName: bio_name
    };
  }

  /**
   * Rule 1: DIRECT ID MATCH
   * Matches biometric emp_code with employee biometric_code
   */
  _ruleDirectIdMatch(bio_id, employee_list) {
    if (!bio_id) return null;

    return employee_list.find(emp =>
      emp.biometric_code &&
      emp.biometric_code.toString().trim().toLowerCase() === bio_id.toString().trim().toLowerCase()
    );
  }

  /**
   * Normalize biometric name
   * Splits into first and last parts
   * 
   * Examples:
   * "Rishabh Y" → { first: "Rishabh", last: "Y" }
   * "R Yadav" → { first: "R", last: "Yadav" }
   * "Rishabh Yadav" → { first: "Rishabh", last: "Yadav" }
   */
  _normalizeName(name) {
    if (!name || typeof name !== 'string') {
      return { first: '', last: '' };
    }

    name = name.trim();
    const parts = name.split(/\s+/);

    if (parts.length === 0) {
      return { first: '', last: '' };
    }

    if (parts.length === 1) {
      return { first: parts[0], last: '' };
    }

    // Multiple parts: assume first word is first name, rest is last name
    return {
      first: parts[0],
      last: parts.slice(1).join(' ')
    };
  }

  /**
   * Rule 3: FIRST NAME EXACT MATCH
   * Filter employees where firstName matches (case-insensitive)
   */
  _ruleFirstNameExactMatch(bioFirstName, employee_list) {
    if (!bioFirstName) return [];

    return employee_list.filter(emp =>
      emp.firstName &&
      emp.firstName.toLowerCase().trim() === bioFirstName.toLowerCase().trim()
    );
  }

  /**
   * Rule 4: FIRST NAME + SURNAME INITIAL MATCH
   * For multiple same-first-name employees:
   * biometric surname first letter == employee last_name first letter
   */
  _ruleSurnameInitialMatch(normalizedBio, candidates) {
    if (!normalizedBio.last || candidates.length === 0) {
      return candidates;
    }

    const bioLastInitial = normalizedBio.last.charAt(0).toLowerCase();

    return candidates.filter(emp =>
      emp.lastName &&
      emp.lastName.charAt(0).toLowerCase() === bioLastInitial
    );
  }

  /**
   * Rule 5: FIRST NAME + LAST NAME PREFIX MATCH
   * Match "Yadav" vs "Y"
   * Match "Kumar" vs "Ku..."
   */
  _ruleLastNamePrefixMatch(normalizedBio, candidates) {
    if (!normalizedBio.last || candidates.length === 0) {
      return candidates;
    }

    const bioLastName = normalizedBio.last.toLowerCase().trim();

    return candidates.filter(emp => {
      if (!emp.lastName) return false;

      const empLastName = emp.lastName.toLowerCase().trim();

      // Exact match
      if (empLastName === bioLastName) return true;

      // Prefix match (at least 3 characters)
      const minLen = Math.min(3, bioLastName.length, empLastName.length);
      if (bioLastName.substring(0, minLen) === empLastName.substring(0, minLen)) {
        return true;
      }

      return false;
    });
  }

  /**
   * Rule 6: FUZZY MATCH (Levenshtein distance)
   * Threshold ≥ 0.8 similarity
   * 
   * Match examples:
   * "Rishab" ↔️ "Rishabh" (typo)
   * "Rahul K." ↔️ "Rahul Kadam" (truncated)
   */
  _ruleFuzzyMatch(bioName, employee_list) {
    if (!bioName) return [];

    const bioNameLower = bioName.toLowerCase().trim();

    const matches = employee_list
      .map(emp => {
        const fullName = `${emp.firstName || ''} ${emp.lastName || ''}`.toLowerCase().trim();
        const firstName = (emp.firstName || '').toLowerCase().trim();

        // Calculate similarity for full name
        const fullNameSimilarity = this._calculateSimilarity(bioNameLower, fullName);
        
        // Calculate similarity for first name
        const firstNameSimilarity = this._calculateSimilarity(bioNameLower, firstName);

        // Use the higher similarity
        const similarity = Math.max(fullNameSimilarity, firstNameSimilarity);

        return {
          employee: emp,
          similarity: similarity,
          fullName: fullName,
          firstName: firstName
        };
      })
      .filter(m => m.similarity >= this.fuzzyThreshold)
      .sort((a, b) => b.similarity - a.similarity);

    return matches;
  }

  /**
   * Calculate Levenshtein similarity (0-1)
   * Uses normalized Levenshtein distance
   */
  _calculateSimilarity(str1, str2) {
    if (!str1 || !str2) return 0;

    const distance = new Levenshtein(str1, str2).distance;
    const maxLen = Math.max(str1.length, str2.length);

    // Normalized similarity: 1 - (distance / maxLen)
    const similarity = 1 - (distance / maxLen);

    return Math.max(0, Math.min(1, similarity));
  }

  /**
   * Debug logging
   */
  _log(message) {
    if (this.debug) {
      console.log(`[BiometricResolver] ${message}`);
    }
  }

  /**
   * Batch mapping for multiple biometric records
   */
  async batchMapBiometricToEmployees(biometricRecords, employee_list) {
    const results = {
      successful: [],
      failed: [],
      ambiguous: [],
      summary: {
        total: biometricRecords.length,
        matched: 0,
        failed: 0,
        ambiguous: 0,
        byType: {}
      }
    };

    for (const record of biometricRecords) {
      const result = await this.mapBiometricToEmployee(
        record.bio_id || record.emp_code,
        record.bio_name || record.name,
        employee_list
      );

      if (result.success) {
        results.successful.push({
          biometricRecord: record,
          mappingResult: result
        });
        results.summary.matched++;
        results.summary.byType[result.matchType] = (results.summary.byType[result.matchType] || 0) + 1;
      } else if (result.errorCode === 'AMBIGUOUS_MATCH') {
        results.ambiguous.push({
          biometricRecord: record,
          mappingResult: result
        });
        results.summary.ambiguous++;
      } else {
        results.failed.push({
          biometricRecord: record,
          mappingResult: result
        });
        results.summary.failed++;
      }
    }

    return results;
  }
}

module.exports = BiometricIdentityResolver;
