import { useEffect, useState } from "react";
import * as api from "@/lib/api";

export function useAuth() {
  const [user, setUser] = useState<api.UserProfile | null>({
    id: "user_123",
    name: "Rahul",
    email: "rahul@example.com",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    api.getMe().then(res => {
      if (res.success && res.data) {
        setUser(res.data);
      }
      setLoading(false);
    }).catch(err => {
      setError(err);
      setLoading(false);
    });
  }, []);

  const logout = async () => {
    localStorage.removeItem("supabase_access_token");
    sessionStorage.removeItem("manus-cookie");
    setUser(null);
  };

  return {
    user,
    loading,
    error,
    logout,
    isAuthenticated: Boolean(user),
  };
}
