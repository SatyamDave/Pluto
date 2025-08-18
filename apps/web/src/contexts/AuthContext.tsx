import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';
import posthog from 'posthog-js';

interface User {
  id: string;
  email: string;
  tier: string;
  subscription_status: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Set up axios defaults
  axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Add auth token to requests
  axios.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Handle auth errors
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('auth_token');
        setUser(null);
      }
      return Promise.reject(error);
    }
  );

  const login = async (email: string, password: string) => {
    try {
      const response = await axios.post('/auth/login', { email, password });
      const { access_token } = response.data;
      
      localStorage.setItem('auth_token', access_token);
      
      // Fetch user profile
      const userResponse = await axios.get('/user/profile');
      const userData = userResponse.data;
      
      setUser(userData);
      
      // Track login event
      posthog.capture('user_login', {
        email: userData.email,
        tier: userData.tier,
      });
      
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const signup = async (email: string, password: string) => {
    try {
      const response = await axios.post('/auth/signup', { email, password });
      const { access_token } = response.data;
      
      localStorage.setItem('auth_token', access_token);
      
      // Fetch user profile
      const userResponse = await axios.get('/user/profile');
      const userData = userResponse.data;
      
      setUser(userData);
      
      // Track signup event
      posthog.capture('user_signup', {
        email: userData.email,
        tier: userData.tier,
      });
      
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
    
    // Track logout event
    if (user) {
      posthog.capture('user_logout', {
        email: user.email,
        tier: user.tier,
      });
    }
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...userData });
    }
  };

  // Check for existing token on app load
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      axios.get('/user/profile')
        .then((response) => {
          setUser(response.data);
        })
        .catch(() => {
          localStorage.removeItem('auth_token');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
