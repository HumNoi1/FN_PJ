"use client";

import React, { useEffect, useState } from "react";
import { NotebookText, Plus, GraduationCap, CircleAlert, Trash2 } from "lucide-react";
import Nav from "@/components/Nav";
import Link from "next/link";
import supabase from "@/lib/supabase";

const Dashboards = () => {
  const [classes, setClasses] = useState([]);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchClasses = async () => {
    const { data, error } = await supabase.from("classes").select("*");
    if (!error) setClasses(data);
  };

  useEffect(() => {
    fetchClasses();
  }, []);

  const handleDelete = async (e, classId) => {
    e.preventDefault();
    try {
      setIsDeleting(true);
      
      const { data: teacherFiles } = await supabase.storage
        .from('teacher-resources')
        .list(classId.toString());
        
      const { data: studentFiles } = await supabase.storage
        .from('student-submissions')
        .list(classId.toString());

      if (teacherFiles?.length) {
        await supabase.storage
          .from('teacher-resources')
          .remove(teacherFiles.map(file => `${classId}/${file.name}`));
      }

      if (studentFiles?.length) {
        await supabase.storage
          .from('student-submissions')
          .remove(studentFiles.map(file => `${classId}/${file.name}`));
      }

      await supabase.from("classes").delete().eq("id", classId);
      setClasses(classes.filter(c => c.id !== classId));
    } catch (err) {
      console.error("Delete error:", err);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex">
      <Nav />
      <div className="flex-grow p-8 bg-slate-800 min-h-screen w-screen">
        <h1 className="text-2xl font-semibold text-white mb-8">Class</h1>
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-3">
            <Link href="/addclass" className="w-full h-40 rounded-xl border-2 border-slate-600 flex items-center justify-center hover:bg-slate-700 transition-colors group">
              <div className="flex flex-col items-center space-y-2">
                <Plus className="w-8 h-8 text-slate-400 group-hover:text-slate-300" />
                <span className="text-sm font-medium text-slate-400 group-hover:text-slate-300">เพิ่มคลาสใหม่</span>
              </div>
            </Link>
          </div>

          {classes.map((classItem) => (
            <div key={classItem.id} className="col-span-3">
              <Link href={`/dashboards/class/${classItem.id}`}>
                <div className="relative w-full h-40 rounded-xl bg-blue-600 p-5 flex flex-col justify-between hover:bg-blue-700 transition-colors cursor-pointer group shadow-lg">
                  <button
                    onClick={(e) => handleDelete(e, classItem.id)}
                    disabled={isDeleting}
                    className="absolute top-3 right-3 p-2 rounded-full bg-blue-700 text-white opacity-0 group-hover:opacity-100 hover:bg-red-500 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <NotebookText className="w-5 h-5 text-blue-200" />
                      <h2 className="text-lg font-semibold text-white">{classItem.name}</h2>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <GraduationCap className="w-4 h-4 text-blue-200" />
                      <p className="text-sm font-medium text-blue-100">{classItem.term}</p>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <CircleAlert className="w-4 h-4 text-blue-200" />
                      <p className="text-sm font-medium text-blue-100">{classItem.subject}</p>
                    </div>
                  </div>
                </div>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboards;