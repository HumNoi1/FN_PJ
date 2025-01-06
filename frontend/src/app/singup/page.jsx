'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Webhook } from 'lucide-react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

export default function SignUpPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();
  const supabase = createClientComponentClient();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Step 1: Sign up with Supabase auth
      const { data: { user }, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (signUpError) throw signUpError;

      if (user) {
        // Step 2: Sign in to get the session
        const { data: { session }, error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password
        });

        if (signInError) throw signInError;

        if (session) {
          // Step 3: Now insert into users table
          const { error: userError } = await supabase
            .from('users')
            .insert([
              {
                id: user.id,
                email: email,
                full_name: fullName,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              }
            ]);

          if (userError) throw userError;
        }
      }

      // Step 4: Sign out after successful registration
      await supabase.auth.signOut();

      // Redirect to login page with success message
      router.push('/login?message=Check your email to confirm your account');
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A1628] flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8">
        {/* Logo */}
        <div className="flex flex-col items-center">
          <div className="bg-[#1C2A3F] p-3 rounded-lg">
            <Webhook className="w-8 h-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-white">
            Create an account
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Please enter your details to sign up
          </p>
        </div>

        {/* Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-2 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="fullName" className="text-sm font-medium text-slate-300">
                Full Name
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="mt-1 block w-full rounded-lg bg-[#1C2A3F] border border-slate-700 
                         px-4 py-2.5 text-white placeholder:text-slate-400 
                         focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                placeholder="Enter your full name"
              />
            </div>

            <div>
              <label htmlFor="email" className="text-sm font-medium text-slate-300">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full rounded-lg bg-[#1C2A3F] border border-slate-700 
                         px-4 py-2.5 text-white placeholder:text-slate-400 
                         focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                placeholder="Enter your email"
              />
            </div>

            <div>
              <label htmlFor="password" className="text-sm font-medium text-slate-300">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full rounded-lg bg-[#1C2A3F] border border-slate-700 
                         px-4 py-2.5 text-white placeholder:text-slate-400 
                         focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                placeholder="Create a password"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg
                     text-sm font-medium text-white bg-blue-500 hover:bg-blue-600 
                     focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                     focus:ring-offset-[#0A1628] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating account...' : 'Sign up'}
          </button>

          <p className="text-center text-sm text-slate-400">
            Already have an account?{' '}
            <button 
              type="button"
              onClick={() => router.push('/login')}
              className="text-blue-500 hover:text-blue-400"
            >
              Sign in
            </button>
          </p>
        </form>
      </div>
    </div>
  );
}