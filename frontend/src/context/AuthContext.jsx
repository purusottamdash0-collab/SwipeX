import React, { createContext, useContext, useState, useEffect } from 'react';
import API from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('swipex_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('swipex_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const res = await API.get('/auth/me');
          setUser(res.data);
          localStorage.setItem('swipex_user', JSON.stringify(res.data));
        } catch (err) {
          logout();
        }
      }
      setLoading(false);
    };
    initAuth();
  }, [token]);

  useEffect(() => {
    const handleAuthFailure = () => {
      logout();
    };
    window.addEventListener('swipex_auth_failure', handleAuthFailure);
    return () => {
      window.removeEventListener('swipex_auth_failure', handleAuthFailure);
    };
  }, []);

  const login = async (email, password) => {
    const res = await API.post('/auth/login', { email, password });
    const { access_token, refresh_token, user: userData } = res.data;
    localStorage.setItem('swipex_token', access_token);
    localStorage.setItem('swipex_refresh_token', refresh_token);
    localStorage.setItem('swipex_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, full_name, role = 'user') => {
    const res = await API.post('/auth/register', { email, password, full_name, role });
    const { access_token, refresh_token, user: userData } = res.data;
    localStorage.setItem('swipex_token', access_token);
    localStorage.setItem('swipex_refresh_token', refresh_token);
    localStorage.setItem('swipex_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const googleLogin = async (idToken, role = 'user') => {
    const res = await API.post('/auth/google', {
      email: 'temp-google@swipex.io',
      fullName: 'Temp Google User',
      googleToken: idToken,
      role: role
    });
    const { access_token, refresh_token, user: userData } = res.data;
    localStorage.setItem('swipex_token', access_token);
    localStorage.setItem('swipex_refresh_token', refresh_token);
    localStorage.setItem('swipex_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    // Clear localStorage & sessionStorage
    localStorage.clear();
    sessionStorage.clear();
    
    // Clear all cookies
    document.cookie.split(";").forEach((c) => {
      document.cookie = c
        .replace(/^ +/, "")
        .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });

    // Reset caches if present
    if (window.QueryClient) {
      try { window.QueryClient.clear(); } catch (e) {}
    }

    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, googleLogin, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
