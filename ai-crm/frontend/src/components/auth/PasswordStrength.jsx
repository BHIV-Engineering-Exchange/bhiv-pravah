import React from 'react';
import { Check, X } from 'lucide-react';

const PasswordStrength = ({ password }) => {
  const requirements = [
    { label: 'At least 8 characters', test: (pwd) => pwd.length >= 8 },
    { label: 'One uppercase letter', test: (pwd) => /[A-Z]/.test(pwd) },
    { label: 'One lowercase letter', test: (pwd) => /[a-z]/.test(pwd) },
    { label: 'One number', test: (pwd) => /[0-9]/.test(pwd) },
    { label: 'One special character', test: (pwd) => /[!@#$%^&*(),.?":{}|<>]/.test(pwd) }
  ];

  const passedRequirements = requirements.filter(req => req.test(password)).length;
  const strength = passedRequirements === 0 ? 0 : 
                   passedRequirements <= 2 ? 1 : 
                   passedRequirements <= 3 ? 2 : 
                   passedRequirements === 4 ? 3 : 4;

  const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['', 'bg-destructive', 'bg-warning', 'bg-info', 'bg-success'];

  return (
    <div className="space-y-3">
      {/* Strength Bar */}
      {password && (
        <div className="space-y-2">
          <div className="flex gap-1">
            {[1, 2, 3, 4].map((level) => (
              <div
                key={level}
                className={`h-1 flex-1 rounded-full transition-colors ${
                  level <= strength ? strengthColors[strength] : 'bg-muted'
                }`}
              />
            ))}
          </div>
          <p className="text-sm font-medium">
            Password Strength: <span className={strength >= 3 ? 'text-success' : 'text-warning'}>
              {strengthLabels[strength]}
            </span>
          </p>
        </div>
      )}

      {/* Requirements */}
      <div className="space-y-1.5">
        {requirements.map((req, index) => {
          const isPassed = req.test(password);
          return (
            <div key={index} className="flex items-center gap-2 text-sm">
              {isPassed ? (
                <Check className="w-4 h-4 text-success" />
              ) : (
                <X className="w-4 h-4 text-muted-foreground" />
              )}
              <span className={isPassed ? 'text-success' : 'text-muted-foreground'}>
                {req.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PasswordStrength;
