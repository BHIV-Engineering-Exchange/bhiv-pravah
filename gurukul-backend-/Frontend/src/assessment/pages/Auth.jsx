import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { adminAuth } from "../config/admin";

export function SignInPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const {
      success,
      admin,
      error: loginError,
    } = await adminAuth.login(username, password);

    if (success) {
      localStorage.setItem("admin", JSON.stringify(admin));
      navigate("/admin");
    } else {
      setError(loginError || "Invalid username or password");
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen">
      <div className="rounded-2xl border border-white/20 bg-white/10 p-6 w-96">
        <h2 className="text-2xl font-bold mb-4 text-center text-white">
          Admin Login
        </h2>
        {error && (
          <div className="bg-red-500/20 text-red-200 p-3 rounded mb-4">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-white mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-2 rounded bg-white/5 border border-white/10 text-white"
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-white mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 rounded bg-white/5 border border-white/10 text-white"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
}

// Since we only want admin authentication, we'll redirect SignUpPage to SignInPage
export function SignUpPage() {
  const navigate = useNavigate();
  React.useEffect(() => {
    navigate("/sign-in");
  }, [navigate]);

  return null;
}
