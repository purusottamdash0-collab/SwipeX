import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { Sparkles, Mail, Lock, User, UserCheck, Briefcase } from 'lucide-react';

export default function Signup() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [role, setRole] = useState('user');
  const [loading, setLoading] = useState(false);

  const { register, googleLogin } = useAuth();
  const { addToast } = useNotification();
  const navigate = useNavigate();

  useEffect(() => {
    /* global google */
    if (typeof google !== 'undefined') {
      try {
        google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || "369527787342-google-demo-id.apps.googleusercontent.com",
          callback: handleGoogleCredentialResponse,
          cancel_on_tap_outside: false
        });
        
        google.accounts.id.renderButton(
          document.getElementById("googleSignUpButton"),
          { theme: "outline", size: "large", width: "100%", text: "signup_with", shape: "rectangular" }
        );
      } catch (err) {
        console.error("Failed to initialize Google signup button:", err);
      }
    }
  }, [role]);

  const handleGoogleCredentialResponse = async (response) => {
    setLoading(true);
    try {
      await googleLogin(response.credential, role);
      addToast('Google Sign Up successful!', 'success');
      navigate('/swipe');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Google authentication failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 10) {
      setPasswordError('Password must be at least 10 characters');
      return;
    }
    setPasswordError('');
    setLoading(true);
    try {
      await register(email, password, fullName, role);
      addToast('Account created successfully!', 'success');
      navigate('/swipe');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Registration failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 glass-panel p-8 rounded-3xl border border-[#262626] bg-[#181818]/80 shadow-2xl">
        
        <div className="text-center space-y-2">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-tr from-[#FF6B00] to-[#FF8A3D] flex items-center justify-center shadow-[0_4px_15px_rgba(255,107,0,0.35)]">
            <Sparkles className="w-6 h-6 text-white animate-pulse" />
          </div>
          <h2 className="text-3xl font-extrabold text-white">Join SwipeX</h2>
          <p className="text-sm text-[#A8A8A8]">Create your account to unlock AI job matching</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#A8A8A8] mb-1.5">Account Role</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setRole('user')}
                className={`py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                  role === 'user'
                    ? 'bg-[#FF6B00]/10 border-[#FF6B00] text-white shadow-[0_4px_15px_rgba(255,107,0,0.25)]'
                    : 'glass-panel border-[#262626] text-[#A8A8A8] hover:text-white'
                }`}
              >
                <UserCheck className="w-4 h-4" /> Job Seeker
              </button>
              <button
                type="button"
                onClick={() => setRole('recruiter')}
                className={`py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                  role === 'recruiter'
                    ? 'bg-[#FF8A3D]/10 border-[#FF8A3D] text-white shadow-[0_4px_15px_rgba(255,138,61,0.25)]'
                    : 'glass-panel border-[#262626] text-[#A8A8A8] hover:text-white'
                }`}
              >
                <Briefcase className="w-4 h-4" /> Recruiter
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#A8A8A8] mb-1.5">Full Name</label>
            <div className="relative">
              <User className="w-5 h-5 absolute left-3 top-3 text-[#A8A8A8]" />
              <input
                type="text"
                required
                minLength={2}
                maxLength={255}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm focus:outline-none"
                placeholder="Alex Mercer"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#A8A8A8] mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-5 h-5 absolute left-3 top-3 text-[#A8A8A8]" />
              <input
                type="email"
                required
                maxLength={255}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm focus:outline-none"
                placeholder="name@example.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#A8A8A8] mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-5 h-5 absolute left-3 top-3 text-[#A8A8A8]" />
              <input
                type="password"
                required
                minLength={10}
                maxLength={128}
                value={password}
                onChange={(e) => { setPassword(e.target.value); setPasswordError(''); }}
                className={`w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm focus:outline-none ${passwordError ? 'border-red-500/60' : ''}`}
                placeholder="Minimum 10 characters"
              />
            </div>
            {passwordError && (
              <p className="text-xs text-red-400 mt-1" role="alert">{passwordError}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 font-bold text-white bg-gradient-to-r from-[#FF6B00] to-[#FF8A3D] rounded-xl shadow-[0_4px_15px_rgba(255,107,0,0.35)] hover:shadow-[0_4px_25px_rgba(255,107,0,0.55)] transition-all flex items-center justify-center gap-2 hover:scale-[1.02]"
          >
            {loading ? 'Creating Account...' : 'Create Free Account'}
          </button>
        </form>

        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-[#262626]"></div></div>
          <div className="relative flex justify-center text-xs uppercase"><span className="bg-[#121212] px-3 text-[#A8A8A8] rounded-full border border-[#262626]">Or</span></div>
        </div>

        <div id="googleSignUpButton" className="w-full flex justify-center mt-1"></div>

        <p className="text-center text-xs text-[#A8A8A8]">
          Already registered?{' '}
          <Link to="/login" className="text-[#FF6B00] font-bold hover:underline">
            Log In
          </Link>
        </p>

      </div>
    </div>
  );
}
