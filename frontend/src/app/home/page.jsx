import React from 'react';
import { Webhook, BookOpen, Users, Brain } from 'lucide-react';
import Link from 'next/link';

export default function HomePage() {
  // Feature cards data for easy maintenance
  const features = [
    {
      icon: <BookOpen className="w-6 h-6" />,
      title: "Upload Documents",
      description: "Upload and manage your teaching materials and student assignments with ease."
    },
    {
      icon: <Brain className="w-6 h-6" />,
      title: "AI-Powered Analysis",
      description: "Get intelligent insights and comparisons between teacher resources and student submissions."
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Collaborative Learning",
      description: "Foster interaction between teachers and students through our platform."
    }
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative z-10 pb-8 sm:pb-16 md:pb-20 lg:pb-28 xl:pb-32 pt-16">
            <main>
              <div className="text-center">
                <div className="flex justify-center mb-8">
                  <div className="bg-slate-800 p-4 rounded-xl">
                    <Webhook className="w-12 h-12 text-blue-500" />
                  </div>
                </div>
                <h1 className="text-4xl tracking-tight font-extrabold text-white sm:text-5xl md:text-6xl">
                  <span className="block">EduChat Assistant</span>
                  <span className="block text-blue-500 mt-2">AI-Powered Learning Platform</span>
                </h1>
                <p className="mt-3 max-w-md mx-auto text-base text-slate-400 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
                  Enhance your teaching and learning experience with our advanced document analysis 
                  and AI-powered chat system. Upload materials, get insights, and foster better 
                  understanding.
                </p>
                <div className="mt-10 flex justify-center gap-4">
                  <Link href="/login" className="px-8 py-3 text-base font-medium rounded-lg text-white bg-blue-500 hover:bg-blue-600 md:text-lg">
                    Sign In
                  </Link>
                  <Link href="/signup" className="px-8 py-3 text-base font-medium rounded-lg text-blue-500 bg-slate-800 hover:bg-slate-700 md:text-lg">
                    Sign Up
                  </Link>
                </div>
              </div>
            </main>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="bg-slate-800 rounded-xl p-6 text-center">
              <div className="flex justify-center mb-4">
                <div className="bg-blue-500/10 p-3 rounded-lg text-blue-500">
                  {feature.icon}
                </div>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-slate-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-slate-800 mt-20">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="text-center text-slate-400">
            <p>© 2025 EduChat Assistant. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}