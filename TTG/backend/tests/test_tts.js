const fetch = require('node-fetch');

async function testTTS() {
  console.log('Testing TTS endpoint...');
  
  try {
    const response = await fetch('http://localhost:3000/api/tts/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        text: 'Hello! VaaniTTS is now integrated with your dashboard.',
        language: 'en',
        tone: 'excited'
      })
    });

    if (response.ok) {
      console.log('✅ TTS endpoint working!');
      console.log('Audio size:', response.headers.get('content-length'), 'bytes');
    } else {
      console.error('❌ TTS failed:', response.status);
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
    console.log('Make sure backend is running: npm run dev');
  }
}

testTTS();
