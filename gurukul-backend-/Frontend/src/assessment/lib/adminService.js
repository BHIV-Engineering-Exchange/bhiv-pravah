import { supabase } from "./supabaseClient";
import bcrypt from "bcryptjs";

export const adminService = {
  // Create a new admin
  async createAdmin(username, password) {
    try {
      // Hash the password
      const salt = await bcrypt.genSalt(10);
      const password_hash = await bcrypt.hash(password, salt);

      // Insert the admin into the database
      const { data, error } = await supabase
        .from("admins")
        .insert([{ username, password_hash }])
        .select()
        .single();

      if (error) throw error;
      return { data, error: null };
    } catch (error) {
      console.error("Error creating admin:", error);
      return { data: null, error };
    }
  },

  // Login admin
  async loginAdmin(username, password) {
    try {
      // Get admin by username
      const { data: admin, error } = await supabase
        .from("admins")
        .select("*")
        .eq("username", username)
        .single();

      if (error) throw error;

      // Verify password
      const validPassword = await bcrypt.compare(password, admin.password_hash);
      if (!validPassword) {
        throw new Error("Invalid password");
      }

      return { data: admin, error: null };
    } catch (error) {
      console.error("Error logging in:", error);
      return { data: null, error };
    }
  },

  // Check if user is admin
  async isAdmin(username) {
    try {
      const { data, error } = await supabase
        .from("admins")
        .select("username")
        .eq("username", username)
        .single();

      if (error) throw error;
      return { isAdmin: !!data, error: null };
    } catch (error) {
      console.error("Error checking admin status:", error);
      return { isAdmin: false, error };
    }
  },
};
