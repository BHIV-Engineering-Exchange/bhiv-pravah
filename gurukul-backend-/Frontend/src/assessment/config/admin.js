import { supabase } from "../lib/supabaseClient";

export const adminAuth = {
  async login(username, password) {
    try {
      const { data, error } = await supabase
        .from("admins")
        .select("*")
        .eq("username", username)
        .eq("password", password)
        .single();

      if (error) {
        return { success: false, error: error.message };
      }

      if (data) {
        return { success: true, admin: data };
      } else {
        return { success: false, error: "Invalid credentials" };
      }
    } catch (error) {
      return { success: false, error: "Login failed" };
    }
  },

  async isAdmin() {
    const admin = localStorage.getItem("admin");
    if (!admin) return false;

    try {
      const adminData = JSON.parse(admin);
      const { data } = await supabase
        .from("admins")
        .select("*")
        .eq("username", adminData.username)
        .eq("password", adminData.password)
        .single();

      return !!data;
    } catch {
      return false;
    }
  },
};
