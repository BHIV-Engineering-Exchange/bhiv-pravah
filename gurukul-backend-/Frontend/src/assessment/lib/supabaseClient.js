import { supabase as mainSupabase } from "../../supabaseClient";

export const supabase = mainSupabase;
export const SUPABASE_TABLE = import.meta.env.VITE_SUPABASE_TABLE || "students";
export const FORM_CONFIG_TABLE = "form_configurations";
