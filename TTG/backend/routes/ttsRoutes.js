const express = require('express');
const router = express.Router();
const gtts = require('node-gtts');
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const unlink = promisify(fs.unlink);
const https = require('https');

async function translateText(text, targetLang) {
  if (targetLang === 'en') return text;
  
  return new Promise((resolve) => {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
    
    const req = https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          const translated = result[0].map(item => item[0]).join('');
          resolve(translated);
        } catch (e) {
          resolve(text); // fallback to original
        }
      });
    });

    // Handle network errors without crashing
    req.on('error', () => resolve(text));

    // Timeout after 3s — don't wait forever
    req.setTimeout(3000, () => {
      req.destroy();
      resolve(text);
    });
  });
}

router.post('/speak', async (req, res) => {
  const { text, language = 'en' } = req.body;
  
  if (!text) {
    return res.status(400).json({ error: 'Text is required' });
  }

  const tempFile = path.join(__dirname, `../temp_${Date.now()}.mp3`);
  
  try {
    const translatedText = await translateText(text, language);
    const tts = gtts(language);
    
    tts.save(tempFile, translatedText, async function() {
      try {
        res.set('Content-Type', 'audio/mpeg');
        const stream = fs.createReadStream(tempFile);
        stream.pipe(res);
        stream.on('end', async () => {
          try { await unlink(tempFile); } catch(e) {}
        });
      } catch (err) {
        res.status(500).json({ error: 'Failed to send audio' });
        try { await unlink(tempFile); } catch(e) {}
      }
    });
  } catch (error) {
    res.status(500).json({ error: 'TTS generation failed' });
  }
});

module.exports = router;
