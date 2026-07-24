import React, { createContext, useContext, useEffect, useState, type PropsWithChildren, type ReactElement } from "react";
import { apiClient } from "@/api/client";

export type AuthUser = {
  id: string;
  username: string;
  email: string;
  role: string;
  is_admin: boolean;
};

type AuthContextType = {
  user: AuthUser | null;
  token: string | null;
  isAdmin: boolean;
  isLoading: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren): ReactElement {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("atlasai_token"));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadUser() {
      const storedToken = localStorage.getItem("atlasai_token");
      if (!storedToken) {
        setUser(null);
        setIsLoading(false);
        return;
      }
      try {
        const response = await apiClient.get<AuthUser>("/auth/me");
        setUser(response.data);
      } catch (err) {
        localStorage.removeItem("atlasai_token");
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    loadUser();
  }, [token]);

  const login = async (usernameOrEmail: string, password: string): Promise<void> => {
    const response = await apiClient.post<{ access_token: string; user: AuthUser }>("/auth/login", {
      username_or_email: usernameOrEmail,
      password: password,
    });

    const newToken = response.data.access_token;
    localStorage.setItem("atlasai_token", newToken);
    setToken(newToken);
    setUser(response.data.user);
  };

  const logout = () => {
    localStorage.removeItem("atlasai_token");
    setToken(null);
    setUser(null);
  };

  const isAdmin = Boolean(user?.is_admin || user?.role?.toLowerCase() === "admin");

  return (
    <AuthContext.Provider value={{ user, token, isAdmin, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
