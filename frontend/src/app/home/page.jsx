import React from 'react';
import { BookOpen, Users, Brain } from 'lucide-react';
import Nav from '@/components/Nav';

export default function HomePage() {
  const features = [
    {
      icon: <BookOpen className="w-6 h-6" />,
      title: "Document Analysis",
      description: "AI-powered PDF analysis and insights"
    },
    {
      icon: <Brain className="w-6 h-6" />,
      title: "Smart Chat",
      description: "Interactive document exploration"
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Resource Hub",
      description: "Efficient material management"
    }
  ];

  return (
    <div className="flex h-screen bg-slate-900 overflow-hidden">
      <Nav />
      <main className="flex-1 relative">
        <div className="h-full flex flex-col">
          {/* Hero Section - 40% of viewport height */}
          <div className="h-2/5 relative flex items-center justify-center bg-gradient-to-r from-blue-500/20 to-purple-500/20">
            <div className="text-center px-4">
              <h1 className="text-4xl md:text-5xl font-extrabold text-white">
                <span className="block">AI-Powered</span>
                <span className="block text-blue-400">Document Analysis</span>
              </h1>
              <p className="mt-4 text-lg text-slate-300">
                Transform your educational content with advanced AI analysis
              </p>
            </div>
          </div>

          {/* Features and Tech Stack - 60% of viewport height */}
          <div className="h-3/5 flex flex-col">
            {/* Features Grid */}
            <div className="flex-1 px-4 py-6">
              <div className="grid md:grid-cols-3 gap-6 h-full max-w-7xl mx-auto">
                {features.map((feature, index) => (
                  <div key={index} 
                       className="bg-slate-800/90 backdrop-blur-sm rounded-xl p-6 flex flex-col items-center justify-center transform hover:-translate-y-1 transition-all duration-300">
                    <div className="bg-blue-500/10 p-3 rounded-lg text-blue-400 mb-4">
                      {feature.icon}
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                    <p className="text-slate-400 text-center">{feature.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Tech Stack - Fixed height */}
            <div className="h-24 bg-slate-800/50 backdrop-blur-sm">
              <div className="h-full max-w-7xl mx-auto px-4 flex items-center justify-around">
                {['Next.js', 'Python', 'Supabase', 'ChromaDB'].map((tech, index) => (
                  <div key={index} className="text-center">
                    <p className="text-white font-medium">{tech}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}