import { useEffect } from "react";
import { refreshSocketAuth } from "../socket/socket";
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export default function useJwtAuth() {
  useEffect(() => {
    async function getToken() {
      // Check if token already exists and is valid
      const existingToken = localStorage.getItem("token");
      if (existingToken) {
        try {
          // Decode token to check expiry
          const payload = JSON.parse(atob(existingToken.split('.')[1]));
          const expiresAt = payload.exp * 1000;
          
          // If token expires in more than 1 day, keep it (static token)
          if (expiresAt - Date.now() > 24 * 60 * 60 * 1000) {
            console.log("[AUTH] Using static token");
            refreshSocketAuth();
            return;
          }
        } catch (err) {
          console.log("[AUTH] Invalid token, fetching new one");
        }
      }

      try {
        const isAdmin = sessionStorage.getItem("asAdmin") === "true";

        const id = isAdmin
          ? "admin"
          : sessionStorage.getItem("uid") ||
            (() => {
              const u = "user_" + Math.random().toString(36).slice(2, 6);
              sessionStorage.setItem("uid", u);
              return u;
            })();

        const res = await fetch(`${BACKEND_URL}/auth/token`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ userId: id }),
        });

        if (!res.ok) {
          throw new Error(`Backend returned ${res.status}`);
        }

        const { token } = await res.json();
        localStorage.setItem("token", token);
        refreshSocketAuth();
      } catch (err) {
        console.error("[AUTH ERROR] Backend not reachable:", err.message);
        console.log("Please ensure backend is running on", BACKEND_URL);
      }
    }

    getToken();
  }, []);
}
