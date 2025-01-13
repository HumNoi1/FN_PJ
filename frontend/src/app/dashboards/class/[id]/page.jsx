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
  const [selectedFile, setSelectedFile] = useState(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDocumentsReady, setIsDocumentsReady] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');

  // File upload functions
  const [uploadingTeacher, setUploadingTeacher] = useState(false);
  const [uploadingStudent, setUploadingStudent] = useState(false);

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

        // Fetch teacher and student files uploads
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

  const handleFileUploads = async (event, fileType) => {
    const isTeacher = fileType === 'teacher';
    const uploadState = isTeacher ? setUploadingTeacher : setUploadingStudent;
    const fileState = isTeacher ? setTeacherFiles : setStudentFiles;
    const bucketName = isTeacher ? 'teacher-resources' : 'student-submissions';

    try {
      uploadState(true);
      setError(null);
      const file = event.target.files[0];

      // validate file ype
      if (file.type !== 'application/pdf') {
        throw new Error('Only PDF files are allowed');
      }

      // upload file to Supabase
      const { data, uploadData, error: uploadsError } = await supabase
        .storage
        .from(bucketName)
        .upload(`${params.id}/${file.name}`, file);

      if (uploadsError) throw uploadsError;

      // check if file need RAG processing (only teacher files)
      if (isTeacher) {
        const statusResponse = await fetch(`http://localhost:8000/status/${file.name}`);
        const statusData = await statusResponse.json();

        // process with RAG if not already processed
        if (!statusData.is_processed) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('is_teacher', String(isTeacher));

          const processResponse = await fetch('http://localhost:8000/process-pdf', {
            method: 'POST',
            body: formData,
          });

          if (!processResponse.ok) {
            // Cleanup if processing fails
            await supabase.storage
              .from(bucketName)
              .remove([`${params.id}/${file.name}`]);

            const errorData = await processResponse.json();
            throw new Error(errorData.detail || 'Failed to process file');
          }
        }
      }

      // update file state
      const { data: files } = await supabase.storage
        .from(bucketName)
        .list(params.id);

      fileState(files || []);
    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Failed to upload file');
    } finally {
      uploadState(false);
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

  // file selection handler with RAG status check
  const handleFileSelect = async (file) => {
    try {
      setSelectedFile(file);
      setAnswer('');
      setQuestion('');
      setIsProcessing(true);
      setIsDocumentsReady(false);
      setError(null);

      //check RAG status
      const statusResponse = await fetch(`http://localhost:8000/status/${file.name}`);
      const statusData = await statusResponse.json();

      if (!statusData.is_processed) {
        // Downloads and processes the file if not already processed
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
      console.error('Error:', err);
      setError(err.message || 'Failed to select file');
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
      <main className="flex-1 p-4">
        <div className="grid grid-cols-12 gap-4 h-full">
          {/* Left Column - Teacher Files */}
          <div className="col-span-3 space-y-4">
            <section className="bg-slate-800 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Teacher Files</h2>
              <label className="block w-full p-3 border-2 border-dashed border-slate-600 rounded-lg hover:border-blue-500 transition-all cursor-pointer group mb-4">
                <input
                  type="file"
                  onChange={(e) => handleFileUploads(e, 'teacher')}
                  disabled={uploadingTeacher}
                  className="hidden"
                />
                <div className="flex flex-col items-center justify-center space-y-2 text-slate-400 group-hover:text-blue-500">
                  <Upload className="w-6 h-6" />
                  <span className="text-sm">{uploadingTeacher ? 'Uploading...' : 'Upload File'}</span>
                </div>
              </label>
              <div className="space-y-2">
                {teacherFiles.map((file) => (
                  <div key={file?.name} className="flex items-center justify-between p-2 bg-slate-700/50 rounded-lg text-sm">
                    <div className="flex items-center space-x-2 flex-1 min-w-0">
                      <a href={getFileUrl(file?.name, true)} className="text-white hover:text-blue-400 truncate">
                        {file?.name}
                      </a>
                      {file?.name?.toLowerCase().endsWith('.pdf') && (
                        <button
                          onClick={() => handleFileSelect(file)}
                          className="p-1 text-slate-400 hover:text-blue-400"
                        >
                          <MessageCircle className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteFile(file?.name, true)}
                      className="p-1 text-slate-400 hover:text-red-400"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Middle Column - Chat */}
          <div className="col-span-6 space-y-4">
            <section className="bg-slate-800 rounded-lg p-4 h-full">
              <div className="flex flex-col h-full">
                <h2 className="text-lg font-semibold text-white mb-4">
                  {selectedFile ? `Chat about ${selectedFile.name}` : 'Select a file to start chatting'}
                </h2>
                
                {selectedFile && (
                  <>
                    <div className="flex-1 mb-4 overflow-auto">
                      {answer && (
                        <div className="p-4 bg-slate-700 rounded-lg mb-4">
                          <div className="text-white whitespace-pre-wrap">{answer}</div>
                        </div>
                      )}
                    </div>

                    <div className="space-y-4">
                      <textarea
                        value={customPrompt}
                        onChange={(e) => setCustomPrompt(e.target.value)}
                        className="w-full p-3 rounded-lg bg-slate-700 text-white border border-slate-600 focus:border-blue-500"
                        placeholder="Custom prompt (optional)"
                        rows="2"
                      />
                      
                      <div className="flex space-x-2">
                        <textarea
                          value={question}
                          onChange={(e) => setQuestion(e.target.value)}
                          disabled={!isDocumentsReady || isProcessing}
                          className="flex-1 p-3 rounded-lg bg-slate-700 text-white border border-slate-600 focus:border-blue-500"
                          placeholder={isProcessing ? 'Processing...' : 'Ask a question'}
                          rows="2"
                        />
                        <button
                          onClick={handleAskQuestion}
                          disabled={isQuerying || !question.trim() || !isDocumentsReady || isProcessing}
                          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
                        >
                          {isQuerying ? 'Searching...' : 'Ask'}
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </section>
          </div>

          {/* Right Column - Student Files */}
          <div className="col-span-3 space-y-4">
            <section className="bg-slate-800 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Student Files</h2>
              <label className="block w-full p-3 border-2 border-dashed border-slate-600 rounded-lg hover:border-blue-500 transition-all cursor-pointer group mb-4">
                <input
                  type="file"
                  onChange={(e) => handleFileUploads(e, 'student')}
                  disabled={uploadingStudent}
                  className="hidden"
                />
                <div className="flex flex-col items-center justify-center space-y-2 text-slate-400 group-hover:text-blue-500">
                  <Upload className="w-6 h-6" />
                  <span className="text-sm">{uploadingStudent ? 'Uploading...' : 'Upload File'}</span>
                </div>
              </label>
              <div className="space-y-2">
                {studentFiles?.map((file) => (
                  <div key={file?.name} className="flex items-center justify-between p-2 bg-slate-700/50 rounded-lg text-sm">
                    <a href={getFileUrl(file?.name, false)} className="text-white hover:text-blue-400 truncate">
                      {file?.name}
                    </a>
                    <button
                      onClick={() => handleDeleteFile(file?.name, false)}
                      className="p-1 text-slate-400 hover:text-red-400"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ClassDetail