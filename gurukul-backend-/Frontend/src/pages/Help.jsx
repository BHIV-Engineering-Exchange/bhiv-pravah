import React from 'react';
import Sidebar from '../components/Sidebar';
import { FaBook, FaComments, FaBrain, FaClipboardCheck, FaLightbulb, FaQuestionCircle } from 'react-icons/fa';

const Help = () => {
    const features = [
        {
            icon: FaComments,
            title: 'Chatbot',
            description: 'Ask questions and get AI-powered answers to help with your studies.',
            howTo: [
                'Click on "Chatbot" in the sidebar',
                'Type your question in the message box',
                'Press Enter or click Send',
                'The AI will respond with helpful information'
            ]
        },
        {
            icon: FaBrain,
            title: 'Document Summarizer',
            description: 'Upload PDFs and get AI-generated summaries and flashcards.',
            howTo: [
                'Go to "Summarizer" page',
                'Click "Upload PDF" and select your document',
                'Wait for the AI to process it',
                'Review the summary and generate flashcards if needed'
            ]
        },
        {
            icon: FaClipboardCheck,
            title: 'Test Generator',
            description: 'Create custom quizzes on any subject to test your knowledge.',
            howTo: [
                'Navigate to "Test Generator"',
                'Enter subject, topic, and difficulty level',
                'Click "Generate Quiz"',
                'Answer the questions and submit to see your score'
            ]
        },
        {
            icon: FaLightbulb,
            title: 'Flashcards',
            description: 'Review and master concepts with spaced repetition flashcards.',
            howTo: [
                'Go to "Flashcards" page',
                'Review cards by clicking "Show Answer"',
                'Rate your confidence (Easy, Medium, Hard)',
                'Cards you struggle with will appear more frequently'
            ]
        }
    ];

    return (
        <div className=\"flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20\">
            < Sidebar />

            <main className=\"flex-grow animate-fade-in-up\" style={{ animationDelay: '0.2s' }}>
                < div className =\"mb-6 sm:mb-8\">
                    < h2 className =\"text-2xl sm:text-3xl font-bold font-heading text-white mb-2\">
    Help & Guides
                    </h2 >
    <p className=\"text-gray-300 text-sm sm:text-base\">
                        Learn how to use Gurukul's features effectively
                    </p >
                </div >

    {/* Quick Start */ }
    < div className =\"glass-panel p-6 rounded-2xl border border-accent/30 mb-6\">
        < div className =\"flex items-center gap-3 mb-4\">
            < FaBook className =\"text-accent text-2xl\" />
                < h3 className =\"text-xl font-bold text-white\">Quick Start Guide</h3>
                    </div >
    <ol className=\"space-y-3 text-gray-300\">
        < li className =\"flex gap-3\">
            < span className =\"text-accent font-bold\">1.</span>
                < span > Sign in with your account to access all features</span >
                        </li >
    <li className=\"flex gap-3\">
        < span className =\"text-accent font-bold\">2.</span>
            < span > Follow the learning journey on your Dashboard: Enter → Learn → Practice → Reflect → Improve</span >
                        </li >
    <li className=\"flex gap-3\">
        < span className =\"text-accent font-bold\">3.</span>
            < span > Use the "Next Step" card to guide your learning path</span >
                        </li >
    <li className=\"flex gap-3\">
        < span className =\"text-accent font-bold\">4.</span>
            < span > Track your progress and reflect on your learning regularly</span >
                        </li >
                    </ol >
                </div >

    {/* Feature Guides */ }
    < div className =\"grid grid-cols-1 lg:grid-cols-2 gap-6\">
{
    features.map((feature, index) => (
        <div key={index} className=\"glass-panel p-6 rounded-2xl border border-white/10\">
    < div className =\"flex items-center gap-3 mb-4\">
    < div className =\"w-12 h-12 rounded-xl bg-accent/20 flex items-center justify-center\">
    < feature.icon className =\"text-accent text-xl\" />
                                </div >
        <h3 className=\"text-lg font-bold text-white\">{feature.title}</h3>
                            </div >

        <p className=\"text-gray-300 text-sm mb-4\">{feature.description}</p>

    < div className =\"space-y-2\">
    < p className =\"text-accent text-sm font-semibold\">How to use:</p>
    < ol className =\"space-y-2\">
                                    {
            feature.howTo.map((step, i) => (
                <li key={i} className=\"text-gray-400 text-sm flex gap-2\">
            < span className =\"text-accent\">{i + 1}.</span>
            < span > { step }</span >
                                        </li >
                                    ))
}
                                </ol >
                            </div >
                        </div >
                    ))}
                </div >

    {/* Need More Help */ }
    < div className =\"mt-6 glass-panel p-6 rounded-2xl border border-white/10 text-center\">
        < FaQuestionCircle className =\"text-accent text-4xl mx-auto mb-4\" />
            < h3 className =\"text-xl font-bold text-white mb-2\">Still Need Help?</h3>
                < p className =\"text-gray-300 text-sm mb-4\">
                        Your learning journey is important to us.If you have questions or need assistance, we're here to help.
                    </p >
    <p className=\"text-gray-400 text-sm\">
                        Contact your teacher or administrator for support
                    </p >
                </div >
            </main >
        </div >
    );
};

export default Help;
