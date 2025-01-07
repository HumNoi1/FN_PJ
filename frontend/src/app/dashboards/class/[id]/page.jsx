"use client";

import React, { useEffect, useState } from 'react';
import { ArrowLeft, Upload, FileText, Trash2, MessageCircle } from 'lucide-react';
import Nav from '@/components/Nav';
import Link from 'next/link';
import supabase from '@/lib/supabase';
import { useParams } from 'next/navigation';

const ClassDetail = () => {

  // State variables
  const params = useParams();
  const [classData, setClassData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [teacherFiles, setTeacherFiles] = useState([]);
  const [studentFiles, setStudentFiles] = useState([]);
  const [uploadingTeacher, setUploadingTeacher] = useState(false);
  const [uploadingStudent, setUploadingStudent] = useState(false);

  // Function for Compare PDF
  const [selectedTeacherFile, setSelectedTeacherFile] = useState(null);
  const [selectedStudentFile, setSelectStudentFile] = useState(null);
  const [comparisonResult, setComparisonResult] = useState('');
  const [isComparing, setIsComparing] = useState(false);
  
  // Function for RAG and Chat
  const [selectedFile, setSelectedFile] = useState(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDocumentsReady, setIsDocumentsReady] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');

  // Fetch function
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch class data
        const { data: classDetails, error: classError } = await supabase
          .from('classes')
          .select('*')
          .eq('id', params.id)
          .single();

        if (classError) throw classError;
        setClassData(classDetails);

        // ดึงข้อมูลไฟล์ที่อัพโหลดแล้ว
        const { data: teacherData, error: teacherError } = await supabase
          .storage
          .from('teacher-resources')
          .list(params.id); // list files in class folder

        if (teacherError) throw teacherError;
        setTeacherFiles(teacherData || []);

        const { data: studentData, error: studentError } = await supabase
          .storage
          .from('student-submissions')
          .list(params.id);

        if (studentError) throw studentError;
        setStudentFiles(studentData || []);

      } catch (err) {
        console.error('Error:', err);
        setError('Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [params.id]);

  const handleTeacherUpload = async (event) => {
    try {
      setUploadingTeacher(true);
      setError(null);
      const file = event.target.files[0];
      
      if (file.type !== 'application/pdf') {
        throw new Error('Only PDF files are supported');
      }
  
      // Upload to Supabase storage
      const { data: uploadData, error: uploadError } = await supabase
        .storage
        .from('teacher-resources')
        .upload(`${params.id}/${file.name}`, file);
  
      if (uploadError) throw uploadError;
  
      // Process with ChromaDB
      const formData = new FormData();
      formData.append('file', file);
      formData.append('class_id', params.id); 
  
      const processResponse = await fetch('http://localhost:8000/process-pdf', {
        method: 'POST',
        body: formData,
      });
  
      if (!processResponse.ok) {
        // Rollback storage upload if processing fails
        await supabase.storage
          .from('teacher-resources')
          .remove([`${params.id}/${file.name}`]);
        throw new Error('Failed to process PDF');
      }
  
      // Refresh file list
      const { data: files } = await supabase.storage
        .from('teacher-resources')
        .list(params.id);
  
      setTeacherFiles(files || []);
  
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message);
      event.target.value = '';
    } finally {
      setUploadingTeacher(false);
    }
  };
  
  const handleStudentUpload = async (event) => {
    try {
      setUploadingStudent(true);
      const file = event.target.files[0];
      
      if (file.type !== 'application/pdf') {
        throw new Error('Only PDF files are supported');
      }
  
      // Upload to Supabase storage
      const { data: uploadData, error: uploadError } = await supabase
        .storage
        .from('student-submissions')
        .upload(`${params.id}/${file.name}`, file);
  
      if (uploadError) throw uploadError;
  
      // Update database record
      const { error: dbError } = await supabase
        .from('student_submissions')
        .insert({
          class_id: params.id,
          file_name: file.name,
          file_path: uploadData.path
        });
  
      if (dbError) throw dbError;
  
      // Refresh file list
      const { data: files } = await supabase.storage
        .from('student-submissions')
        .list(params.id);
      
      setStudentFiles(files || []);
  
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message);
    } finally {
      setUploadingStudent(false);
    }
  };

  const handleDeleteFile = async (path, isTeacher) => {
    try {
      if (!isTeacher) {
        // Delete student file from Supabase only
        await supabase.storage
          .from('student-submissions')
          .remove([`${params.id}/${path}`]);
          
        const { data } = await supabase.storage
          .from('student-submissions')
          .list(params.id);
        
        setStudentFiles(data || []);
        return;
      }
  
      // Delete teacher file from both Supabase and ChromaDB
      await supabase.storage
        .from('teacher-resources')
        .remove([`${params.id}/${path}`]);
  
      await fetch(`http://localhost:8000/delete/${path}`, {
        method: 'DELETE'
      });
  
      const { data } = await supabase.storage
        .from('teacher-resources')
        .list(params.id);
  
      setTeacherFiles(data || []);
      
      if (selectedFile?.name === path) {
        setSelectedFile(null);
        setAnswer('');
        setQuestion('');
      }
  
    } catch (err) {
      console.error('Delete error:', err);
      setError('Failed to delete file');
    }
  };

  const getFileUrl = (path, isTeacher) => {
    const bucketName = isTeacher ? 'teacher-resources' : 'student-submissions';
    const { data } = supabase.storage
      .from(bucketName)
      .getPublicUrl(`${params.id}/${path}`);
    return data.publicUrl;
  };

  const handleFileSelect = async (file) => {
    try {
      setSelectedFile(file);
      setAnswer('');
      setQuestion('');
      setIsProcessing(true);
      setIsDocumentsReady(false);
      setError(null);
  
      const statusResponse = await fetch(`http://localhost:8000/status/${file.name}`);
      const statusData = await statusResponse.json();
  
      if (!statusData.is_processed) {
        const { data, error } = await supabase.storage
          .from('teacher-resources')
          .download(`${params.id}/${file.name}`);
        
        if (error) throw error;
  
        const formData = new FormData();
        formData.append('file', new Blob([data], { type: 'application/pdf' }), file.name);
  
        const response = await fetch('http://localhost:8000/process-pdf', {
          method: 'POST',
          body: formData,
        });
  
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to process file');
        }
      }
      
      setIsDocumentsReady(true);
    } catch (err) {
      console.error('Error processing file:', err);
      setError(err.message || 'Failed to process file for RAG');
      setSelectedFile(null);
      setIsDocumentsReady(false);
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleAskQuestion = async () => {
    if (!selectedFile || !question.trim()) {
      setError('Please select a file and enter a question');
      return;
    }
  
    try {
      setIsQuerying(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          question: question.trim(),
          custom_prompt: customPrompt.trim(),
          filename: selectedFile.name
        }),
      });
  
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get answer');
      }
  
      const data = await response.json();
      setAnswer(data.response);
    } catch (err) {
      console.error('Error getting answer:', err);
      setError(err.message || 'Failed to get answer');
    } finally {
      setIsQuerying(false);
    }
  };

  const handleComapre = async () => {
    if (!selectedTeacherFile || !selectedStudentFile) {
      setError('Please select both teacher and student files');
      return;
    }

    try {
      setIsComparing(true);
      setError(null);

      const response = await fetch('http://localhost:8000/compare-pdfs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          teacher_file: selectedTeacherFile.name,
          student_file: selectedStudentFile.name,
          question: question.trim() || null,
          custom_prompt: customPrompt.trim() || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to compare files');
      }

      const data = await response.json();
      setComparisonResult(data.comparison);
    } catch (err) {
      console.error('Error comparing files:', err);
      setError(err.message || 'Failed to compare files');
    } finally {
      setIsComparing(false);
    }
  };

  if (loading) return (
    <div className="flex">
      <Nav />
      <div className="flex-grow p-6 bg-slate-800 min-h-screen w-screen">
        <div className="text-white">Loading...</div>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-slate-900">
    <Nav />
    <main className="flex-1 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <header className="flex items-center justify-between">
          <Link 
            href="/dashboards" 
            className="inline-flex items-center px-4 py-2 text-sm text-slate-400 hover:text-slate-200 transition-colors rounded-lg hover:bg-slate-800"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Link>
        </header>

        {/* Error Alert */}
        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Class Info Card */}
        <section className="bg-slate-800 rounded-xl p-8 shadow-lg">
          <h1 className="text-4xl font-bold text-white mb-8">
            {classData?.name}
          </h1>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-2">
              <h2 className="text-lg font-medium text-slate-400">Term</h2>
              <p className="text-2xl text-white">{classData?.term}</p>
            </div>
            <div className="space-y-2">
              <h2 className="text-lg font-medium text-slate-400">Subject</h2>
              <p className="text-2xl text-white">{classData?.subject}</p>
            </div>
          </div>
        </section>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-12 gap-8">
          {/* Upload Sections */}
          <aside className="lg:col-span-4 space-y-8">
            {/* Teacher Upload */}
            <section className="bg-slate-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-bold text-white mb-6">Teacher Uploads</h2>
              <label className="block w-full p-4 border-2 border-dashed border-slate-600 rounded-xl hover:border-blue-500 transition-all duration-200 cursor-pointer group">
                <input
                  type="file"
                  onChange={handleTeacherUpload}
                  disabled={uploadingTeacher}
                  className="hidden"
                />
                <div className="flex flex-col items-center justify-center space-y-2 text-slate-400 group-hover:text-blue-500">
                  <Upload className="w-8 h-8" />
                  <span>{uploadingTeacher ? 'Uploading...' : 'Upload Teacher File'}</span>
                </div>
              </label>
            </section>

            {/* Student Upload */}
            <section className="bg-slate-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-bold text-white mb-6">Student Uploads</h2>
              <label className="block w-full p-4 border-2 border-dashed border-slate-600 rounded-xl hover:border-blue-500 transition-all duration-200 cursor-pointer group">
                <input
                  type="file"
                  onChange={handleStudentUpload}
                  disabled={uploadingStudent}
                  className="hidden"
                />
                <div className="flex flex-col items-center justify-center space-y-2 text-slate-400 group-hover:text-blue-500">
                  <Upload className="w-8 h-8" />
                  <span>{uploadingStudent ? 'Uploading...' : 'Upload Student File'}</span>
                </div>
              </label>
            </section>
          </aside>

          {/* Files Display */}
          <div className="lg:col-span-8 space-y-8">
            {/* Teacher Files */}
            <section className="bg-slate-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-bold text-white mb-6 flex items-center">
                <FileText className="w-6 h-6 mr-3" />
                Teacher Files
              </h2>
              <div className="space-y-3">
                {teacherFiles.map((file) => (
                  <div key={file?.id || file?.name} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors">
                    <div className="flex items-center space-x-4 flex-1 min-w-0">
                      <a
                        href={getFileUrl(file?.name, true)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-white hover:text-blue-400 truncate"
                      >
                        {file?.name}
                      </a>
                      {file?.name && file.name.toLowerCase().endsWith('.pdf') && (
                        <button
                          onClick={() => handleFileSelect(file)}
                          className={`p-2 text-slate-400 hover:text-blue-400 transition-colors &{
                            selectedFile?.name === file.name
                              ? 'bg-blue-500 text-white'
                              : 'bg-slate-700' 
                            }`}
                        >
                          <MessageCircle className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteFile(file?.name, true)}
                      className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                {teacherFiles.length === 0 && (
                  <p className="text-slate-400 text-center py-8">No teacher files uploaded yet</p>
                )}
              </div>
            </section>

            {/* Student Files */}
            <section className="bg-slate-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-xl font-bold text-white mb-6 flex items-center">
                <FileText className="w-6 h-6 mr-3" />
                Student Files
              </h2>
              <div className="space-y-3">
                {studentFiles?.map((file) => (
                  <div key={file?.id || file?.name} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors">
                    <a
                      href={getFileUrl(file?.name, false)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-white hover:text-blue-400 truncate"
                    >
                      {file?.name}
                    </a>
                    <button
                      onClick={() => handleDeleteFile(file?.name, false)}
                      className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                {!studentFiles?.length && (
                  <p className="text-slate-400 text-center py-8">No student files uploaded yet</p>
                )}
              </div>
            </section>
          </div>
          
          {/* RAG and Chat */}
          {selectedFile && (
            <section className="lg:col-span-12 bg-slate-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-xl font-bold text-white mb-6 flex items-center justify-between">
                <span>ถามเกี่ยวกับ {selectedFile.name}</span>
                {isProcessing && (
                  <span className="text-sm text-blue-400">Processing...</span>
                )}
              </h3>
              
              {/*custom prompt*/}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Custom Prompt (optional)
                </label>
                <textarea
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  className="w-full p-3 rounded-lg bg-slate-700 text-white border border-slate-600 focus:border-blue-500"
                  placeholder='Enter a custom prompt for the model (optional)'
                  rows="2"
                />
              </div>

              {/* Question Input */}
              <div className="space-y-4">
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={!isDocumentsReady || isProcessing}
                  className="w-full p-4 rounded-lg bg-slate-700 text-white border border-slate-600 focus:border-blue-500 disabled:opacity-50"
                  placeholder={
                    isProcessing
                      ? 'Please wait for processing to complete...'
                      : !isDocumentsReady
                        ? 'Enter your question here...'
                        : 'Please wait for processing to complete...'
                  }
                  rows="4"
                />
              </div>

              {/* Ask Question Button */}
              <button
                onClick={handleAskQuestion}
                disabled={isQuerying || !question.trim() || !isDocumentsReady || isProcessing} 
                className="mt-4 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  {isQuerying
                    ? 'กำลังค้นหาคำตอบ...'
                    : isProcessing
                      ? 'กำลังประมวลผลเอกสาร...'
                      : 'ถามคำถาม'}
              </button>

              {/* Ask Question Button */}
              {answer && (
                <div className="mt-6 p-6 bg-slate-700 rounded-lg">
                  <h4 className="teat-sm font-medium text-slate-300 mb-3">คำตอบ</h4>
                  <div className="text-white whitespace-pre-wrap">{answer}</div>
                </div>
              )}

            </section>
          )}

        {/* Comparison Section */}
        {selectedTeacherFile && selectedStudentFile && (
          <section className="lg:col-span-12 bg-slate-800 rounded-xl p-6 shadow-lg">
            <h3 className="text-xl font-bold text-whit mb-6">
              Compare Files
            </h3>

            <div className="flex items-center gap-4 mb-4">
              <span className="text-slate-300">
                Comparing: {selectedTeacherFile.name} ↔ {selectedStudentFile.name}
              </span>
            </div>

            <button
              onClick={handleComapre}
              disabled={isComparing}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              {isComparing ? 'Comparing...' : 'Compare Files'}
            </button>

            {comparisonResult && (
              <div className="mt-6 p-6 bg-slate-700 rounded-lg">
                <h4 className="text-sm font-medium text-slate-300 mb-3">
                  Comparison Result
                </h4>
                <div className="text-white whitespace-pre-wrap">
                  {comparisonResult}
                </div>
              </div>
            )}
          </section>
        )}

        </div>

      </div>
    </main>
  </div>
  );
};

export default ClassDetail