const checkServerConnection = async () => {
    try {
      const response = await fetch('/api/health-check');
      if (!response.ok) {
        throw new Error('Cannot connect to backend server');
      }
      return true;
    } catch (error) {
      console.error('Server connection error:', error);
      return false;
    }
  };
  
  const handleEvaluate = async () => {
    if (!selectedTeacherFile || selectedStudentFiles.length === 0 || !question) {
      alert('กรุณาเลือกไฟล์และกรอกคำถามให้ครบถ้วน');
      return;
    }
  
    setIsLoading(true);
    try {
      // ตรวจสอบการเชื่อมต่อก่อน
      const isServerConnected = await checkServerConnection();
      if (!isServerConnected) {
        throw new Error('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้ กรุณาตรวจสอบว่า Flask server กำลังทำงานอยู่');
      }
  
      const evaluationPromises = selectedStudentFiles.map(async (studentFile) => {
        const response = await fetch('/api/evaluation/evaluate-answer', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            question,
            student_file_id: studentFile.id,
            teacher_file_ids: [selectedTeacherFile.id]
          }),
        });
  
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
  
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
      alert(`เกิดข้อผิดพลาดในการประเมิน: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };