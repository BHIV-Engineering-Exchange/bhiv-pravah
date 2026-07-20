import { useState, useEffect } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { useNavigate, useLocation } from "react-router-dom";
import { supabase, SUPABASE_TABLE } from "../lib/supabaseClient";

/**
 * Component that handles post-authentication redirect logic for students
 * 
 * Flow:
 * 1. Check if student has completed intake form
 * 2. If not completed -> redirect to /intake
 * 3. If completed -> redirect to /assignment or intended destination
 */
export default function StudentRedirect({ children }) {
  const { user, loading: isLoaded } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    async function checkStudentStatus() {
      // Only run if user is loaded
      if (!isLoaded) {
        setIsChecking(false);
        return;
      }

      // If no user, let the ProtectedRoute handle it
      if (!user) {
        setIsChecking(false);
        return;
      }

      try {
        console.log("🔍 Checking student intake status for user:", user.id);

        // Check if student has completed intake by looking for their record
        const { data: studentRecord, error } = await supabase
          .from(SUPABASE_TABLE)
          .select("id, user_id, responses, name, email")
          .eq("user_id", user.id)
          .single();

        if (error && error.code !== "PGRST116") {
          console.error("❌ Error checking student status:", error);
          setIsChecking(false);
          return;
        }

        const hasIntakeData = studentRecord && studentRecord.responses &&
          Object.keys(studentRecord.responses).length > 0;

        console.log("📊 Student status check result:", {
          hasRecord: !!studentRecord,
          hasResponses: hasIntakeData,
          currentPath: location.pathname
        });

        // Handle redirects based on current path and intake status
        const currentPath = location.pathname;

        // If user is on the home page or root and they haven't completed intake
        if ((currentPath === "/" || currentPath === "/home") && !hasIntakeData) {
          console.log("➡️ Redirecting new student to intake");
          navigate("/intake", { replace: true });
          return;
        }

        // If user is trying to access assignment without completing intake
        if (currentPath === "/assignment" && !hasIntakeData) {
          console.log("➡️ Redirecting to intake (assignment requires completed intake)");
          navigate("/intake", { replace: true });
          return;
        }

        // If user is trying to access dashboard without completing intake
        if (currentPath === "/dashboard" && !hasIntakeData) {
          console.log("➡️ Redirecting to intake (dashboard requires completed intake)");
          navigate("/intake", { replace: true });
          return;
        }

        // Allow users to access intake page for editing their profile
        // No longer automatically redirect to assignment if they have intake data
        // This allows profile editing functionality

      } catch (err) {
        console.error("❌ Error in student redirect check:", err);
      } finally {
        setIsChecking(false);
      }
    }

    checkStudentStatus();
  }, [user, isLoaded, navigate, location.pathname]);

  // Show loading state while checking
  if (isChecking) {
    return (
      <div className="flex items-center justify-center min-h-[200px] text-white">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
        <span className="ml-3 text-white/70">Checking your progress...</span>
      </div>
    );
  }

  // Render children normally after check is complete
  return children;
}