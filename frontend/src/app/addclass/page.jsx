"use client";

import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import Nav from '@/components/Nav';
import supabase from '@/lib/supabase';
import { useRouter } from 'next/navigation';

const AddClass = () => {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    term: '',
    subject: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const { error: insertError } = await supabase
        .from('classes')
        .insert([formData])
        .select();

      if (!insertError) router.push('/dashboards');
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="flex">
      <Nav />
      <div className="flex-grow p-8 bg-slate-800 min-h-screen w-screen">
        <div className="max-w-2xl mx-auto">
          <Link 
            href="/dashboards" 
            className="inline-flex items-center text-sm font-medium text-slate-400 hover:text-slate-300 mb-8"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            กลับไปหน้า Dashboard
          </Link>
          
          <form onSubmit={handleSubmit} className="bg-slate-700 p-8 rounded-xl shadow-lg">
            <h1 className="text-2xl font-semibold text-white mb-8">เพิ่มคลาสใหม่</h1>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  ชื่อคลาส
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-slate-600 border border-slate-500 rounded-xl text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  required
                  disabled={loading}
                  placeholder="กรุณากรอกชื่อคลาส"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  ภาคการศึกษา
                </label>
                <input
                  type="text"
                  name="term"
                  value={formData.term}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-slate-600 border border-slate-500 rounded-xl text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  required
                  disabled={loading}
                  placeholder="กรุณากรอกภาคการศึกษา"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  วิชา
                </label>
                <input
                  type="text"
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-slate-600 border border-slate-500 rounded-xl text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  required
                  disabled={loading}
                  placeholder="กรุณากรอกชื่อวิชา"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-4"
              >
                {loading ? 'กำลังเพิ่มคลาส...' : 'เพิ่มคลาส'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddClass;