const { compile } = require('./intentCompiler');

// Test with demo prompts
const prompts = [
  "Make a fast runner with jump and obstacles",
  "Make temple run with jetpack and score",
  "Create an easy platform jump game",
  "Runner with collectibles and coins",
  "Hard fast runner with obstacles to dodge"
];

prompts.forEach((prompt, i) => {
  console.log(`\n--- Demo ${i + 1} ---`);
  console.log(`Input: "${prompt}"`);
  const result = compile(prompt);
  console.log('Output:', JSON.stringify(result, null, 2));
});
