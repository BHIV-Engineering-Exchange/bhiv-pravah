// Profanity detection utility
const badWords = [
    'fuck', 'shit', 'damn', 'bitch', 'ass', 'bastard', 'crap',
    'hell', 'dick', 'piss', 'cock', 'pussy', 'slut', 'whore',
    'fag', 'retard', 'idiot', 'stupid', 'dumb', 'moron',
    // Add more as needed
];

export const containsProfanity = (text) => {
    if (!text) return false;

    const lowerText = text.toLowerCase();

    // Check for exact word matches (with word boundaries)
    return badWords.some(word => {
        const regex = new RegExp(`\\b${word}\\b`, 'i');
        return regex.test(lowerText);
    });
};

export const cleanText = (text) => {
    if (!text) return text;

    let cleanedText = text;
    badWords.forEach(word => {
        const regex = new RegExp(`\\b${word}\\b`, 'gi');
        cleanedText = cleanedText.replace(regex, '***');
    });

    return cleanedText;
};
