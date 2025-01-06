"use client";

import React, { useEffect, useState } from "react";
import { NotebookText, Plus, GraduationCap, CircleAlert } from "lucide-react";
import Nav from "@/components/Nav";
import Link from "next/link";
import supabase from "@/lib/supabase";

const Dashboards = () => {
  const [classes, setClasses] = useState([]);

  useEffect(() => {
    const fetchClasses = async () => {
      const { data, error } = await supabase
        .from("classes")
        .select("*");

      if (error) {
        console.error("Error fetching classes:", error);
      } else {
        setClasses(data);
        // Log the classes data to see what we're getting
        console.log("Fetched classes:", data);
      }
    };

    fetchClasses();
  }, []);

  return (
    <div className="flex">
      <Nav />
      <div className="flex-grow p-6 bg-slate-800 min-h-screen w-screen">
        <div className="grid grid-cols-12 gap-4">
          {/* Add Button */}
          <div className="col-span-3">
            <Link 
              href="/addclass" 
              className="w-full h-32 rounded-lg border-2 border-slate-600 flex items-center justify-center hover:bg-slate-700 transition-colors"
            >
              <Plus className="w-8 h-8 text-slate-400" />
            </Link>
          </div>

          {/* Display Classes */}
          {classes.map((classItem) => {
            // Log each class URL as it's rendered
            const classUrl = `/dashboards/class/${classItem.id}`;
            console.log("Class URL:", classUrl);
            
            return (
              <div key={classItem.id} className="col-span-3">
                <Link href={classUrl}>
                  <div className="w-full h-32 rounded-lg bg-blue-500 p-4 flex flex-col justify-end hover:bg-blue-600 transition-colors cursor-pointer">
                    <div className="flex items-center space-x-2">
                      <NotebookText />
                      <h2 className="text-white font-bold">{classItem.name}</h2>
                    </div>
                    <div className="flex items-center space-x-2 mt-2">
                      <GraduationCap />
                      <p className="text-white">{classItem.term}</p>
                    </div>
                    <div className="flex items-center space-x-2 mt-2">
                      <CircleAlert />
                      <p className="text-white">{classItem.subject}</p>
                    </div>
                  </div>
                </Link>
              </div>
            );            
          })}
        </div>
      </div>
    </div>
  );
};

export default Dashboards;