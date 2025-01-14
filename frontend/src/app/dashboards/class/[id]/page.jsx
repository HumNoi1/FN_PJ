'use client';

import React, { useState } from 'react';
import { Upload, MessageCircle, Trash2, FileText, FileType } from 'lucide-react';
import Nav from '@/components/Nav';
import { FileService } from '@/services/FileService';

const DocumentComparisonPage = () => {
  // State management สำหรับการจัดการไฟล์และการแสดงผล
  const [teacherFiles, setTeacherFiles] = useState([]);
  const [studentFiles, setStudentFiles] = useState([]);
  const [selectedTeacherFile, setSelectedTeacherFile] = useState(null);
  const [selectedStudentFiles, setSelectedStudentFiles] = useState([]);
  const [question, setQuestion] = useState('');
  const [evaluations, setEvaluations] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  // จัดการการอัปโหลดไฟล์
  const handleFileUpload = async (event, fileType) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
        setIsLoading(true);
        
        const fileRecord = await FileService.uploadFile(file, fileType);
        
        if (fileType === FileService.FILE_TYPES.TEACHER) {
            setTeacherFiles(prev => [...prev, fileRecord]);
        } else {
            setStudentFiles(prev => [...prev, fileRecord]);
        }

        alert('ไฟล์ถูกอัปโหลดเรียบร้อยแล้ว');
        
    } catch (error) {
        alert(`เกิดข้อผิดพลาดในการอัปโหลด: ${error.message}`);
    } finally {
        setIsLoading(false);
        event.target.value = '';
    }
  };

  // ฟังก์ชันการประเมิน
  const handleEvaluate = async () => {
    if (!selectedTeacherFile || selectedStudentFiles.length === 0 || !question) {
      alert('กรุณาเลือกไฟล์และกรอกคำถามให้ครบถ้วน');
      return;
    }

    setIsLoading(true);
    try {
      const evaluationPromises = selectedStudentFiles.map(async (studentFile) => {
        const response = await fetch('/api/evaluate-answer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question,
            student_file_id: studentFile.id,
            teacher_file_id: selectedTeacherFile.id
          }),
        });
        return { studentFile, result: await response.json() };
      });

      const results = await Promise.all(evaluationPromises);
      const newEvaluations = {};
      results.forEach(({ studentFile, result }) => {
        if (result.success) {
          newEvaluations[studentFile.id] = result.evaluation;
        }
      });
      setEvaluations(newEvaluations);
    } catch (error) {
      console.error('Error evaluating:', error);
      alert('เกิดข้อผิดพลาดในการประเมิน');
    }
    setIsLoading(false);
  };

  // แสดงผลการประเมินสำหรับนักเรียนแต่ละคน
  const renderEvaluation = (studentFile) => {
    const evaluation = evaluations[studentFile.id];
    if (!evaluation) return null;

    return (
      <div key={studentFile.id} className="bg-slate-700 rounded-lg p-4 mb-4">
        <div className="flex justify-between mb-4">
          <h3 className="text-white font-medium">{studentFile.name}</h3>
          <span className="text-white">คะแนนรวม: {evaluation.total_score}/100</span>
        </div>

        {/* แสดงคะแนนแต่ละด้าน */}
        <div className="space-y-3">
          {Object.entries(evaluation.scores).map(([criterion, score]) => (
            <div key={criterion} className="text-white">
              <div className="flex justify-between mb-1">
                <span>{criterion}</span>
                <span>{score} คะแนน</span>
              </div>
              <div className="w-full bg-slate-600 rounded-full h-2">
                <div
                  className="bg-blue-500 rounded-full h-2"
                  style={{
                    width: `${(score / getMaxScore(criterion)) * 100}%`
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* แสดงข้อเสนอแนะ */}
        <div className="mt-4 text-white">
          <div className="bg-slate-600 rounded-lg p-3 mb-2">
            <p className="font-medium mb-1">คำแนะนำ:</p>
            <p className="text-slate-200">{evaluation.feedback}</p>
          </div>
          <div className="bg-slate-600 rounded-lg p-3">
            <p className="font-medium mb-1">แนวทางการพัฒนา:</p>
            <p className="text-slate-200">{evaluation.improvement_suggestions}</p>
          </div>
        </div>
      </div>
    );
  };

  // Helper function สำหรับคำนวณคะแนนเต็มของแต่ละเกณฑ์
  const getMaxScore = (criterion) => {
    const maxScores = {
      "ความถูกต้องของเนื้อหา": 40,
      "ความครบถ้วนของคำตอบ": 30,
      "การอ้างอิงแนวคิดสำคัญ": 20,
      "การเรียบเรียงเนื้อหา": 10
    };
    return maxScores[criterion] || 10;
  };

  return (
    <div className="flex h-screen bg-slate-900">
      <Nav />
      
      {/* ส่วนซ้าย - ไฟล์อาจารย์ */}
      <div className="w-1/4 p-4 border-r border-slate-700">
        <div className="bg-slate-800 rounded-lg p-4 h-full">
          <h2 className="text-lg font-semibold text-white mb-4">เอกสารอ้างอิง</h2>
          
          {/* ปุ่มอัปโหลดไฟล์ */}
          <label className="block w-full p-3 border-2 border-dashed border-slate-600 rounded-lg hover:border-blue-500 transition-all cursor-pointer group mb-4">
            <input type="file" className="hidden" onChange={(e) => handleFileUpload(e, 'teacher')} accept=".pdf" />
            <div className="flex flex-col items-center justify-center space-y-2 text-slate-400 group-hover:text-blue-500">
              <Upload className="w-6 h-6" />
              <span className="text-sm">อัปโหลดไฟล์อ้างอิง</span>
            </div>
          </label>

          {/* รายการไฟล์อาจารย์ */}
          <div className="space-y-2">
            {teacherFiles.map(file => (
              <div key={file.id} className="flex items-center justify-between p-2 bg-slate-700/50 rounded-lg">
                <div className="flex items-center space-x-2 text-white">
                  <FileText className="w-4 h-4" />
                  <span className="text-sm">{file.name}</span>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedTeacherFile(file)}
                    className={`p-1 ${selectedTeacherFile?.id === file.id ? 'text-blue-400' : 'text-slate-400'}`}
                  >
                    <MessageCircle className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => FileService.deleteFile(file.id)}
                    className="p-1 text-slate-400 hover:text-red-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ส่วนกลาง - แสดงผลการประเมิน */}
      <div className="flex-1 p-4">
        <div className="bg-slate-800 rounded-lg p-4 h-full flex flex-col">
          <h2 className="text-lg font-semibold text-white mb-4">ผลการประเมิน</h2>
          
          {/* พื้นที่แสดงผลการประเมิน */}
          <div className="flex-1 mb-4 overflow-y-auto">
            {selectedStudentFiles.map(renderEvaluation)}
          </div>

          {/* ส่วนป้อนคำถาม */}
          <div className="flex space-x-2">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="flex-1 p-3 rounded-lg bg-slate-700 text-white border border-slate-600 focus:border-blue-500 focus:outline-none"
              placeholder="กรอกคำถามที่ต้องการประเมิน..."
              rows={3}
            />
            <button
              onClick={handleEvaluate}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors self-end disabled:bg-slate-500"
            >
              {isLoading ? 'กำลังประเมิน...' : 'ประเมินคำตอบ'}
            </button>
          </div>
        </div>
      </div>

      {/* ส่วนขวา - ไฟล์นักเรียน */}
      <div className="w-1/4 p-4 border-l border-slate-700">
        <div className="bg-slate-800 rounded-lg p-4 h-full">
          <h2 className="text-lg font-semibold text-white mb-4">คำตอบนักเรียน</h2>
          
          {/* ปุ่มอัปโหลดไฟล์นักเรียน */}
          <label className="block w-full p-3 border-2 border-dashed border-slate-600 rounded-lg hover:border-blue-500 transition-all cursor-pointer group mb-4">
            <input type="file" className="hidden" onChange={(e) => handleFileUpload(e, 'student')} accept=".pdf" />
            <div className="flex flex-col items-center justify-center space-y-2 text-slate-400 group-hover:text-blue-500">
              <Upload className="w-6 h-6" />
              <span className="text-sm">อัปโหลดคำตอบนักเรียน</span>
            </div>
          </label>

          {/* รายการไฟล์นักเรียน */}
          <div className="space-y-2">
            {studentFiles.map(file => (
              <div key={file.id} className="flex items-center justify-between p-2 bg-slate-700/50 rounded-lg">
                <div className="flex items-center space-x-2 text-white">
                  <FileText className="w-4 h-4" />
                  <span className="text-sm">{file.name}</span>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => {
                      const isSelected = selectedStudentFiles.some(f => f.id === file.id);
                      if (isSelected) {
                        setSelectedStudentFiles(prev => prev.filter(f => f.id !== file.id));
                      } else {
                        setSelectedStudentFiles(prev => [...prev, file]);
                      }
                    }}
                    className={`p-1 ${selectedStudentFiles.some(f => f.id === file.id) ? 'text-blue-400' : 'text-slate-400'}`}
                  >
                    <MessageCircle className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => FileService.deleteFile(file.id)}
                    className="p-1 text-slate-400 hover:text-red-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentComparisonPage;