'use client';

import React from "react";
import { Home, Moon, LogOut, Webhook, BookMarked, BotMessageSquare } from "lucide-react";
import Link from "next/link";

const Nav = () => {
  return (
    <nav className="w-16 bg-slate-900 flex flex-col items-center py-4 space-y-6">
      <div className="p-2 text-white">
        <Webhook className="w-6 h-6" />
      </div>
      
      <Link href="/home" className="p-2 text-white hover:bg-slate-700 rounded">
        <Home className="w-6 h-6" />
      </Link>
      
      <Link href="/dashboards" className="p-2 text-white hover:bg-slate-700 rounded">
        <BookMarked className="w-6 h-6"/>
      </Link>
      <Link href="/dashboards/TeacherDashboards" className="p-2 text-white hover:bg-slate-700 rounded">
        <BotMessageSquare className="w-6 h-6" />
      </Link>
      
      <div className="flex-grow" />
      
      <button className="p-2 text-white hover:bg-slate-700 rounded">
        <Moon className="w-6 h-6" />
      </button>
      
      <Link href="/login"
        className="p-2 text-white hover:bg-slate-700 rounded">
        <LogOut className="w-6 h-6" />
      </Link>
    </nav>
  );
};

export default Nav;