import { User } from './user.model';

export interface Doctor {
  id: number;
  doctor_id: string;
  license_number: string;
  department_id: number;
  user?: User;
  full_name?: string;
  qualification?: string;
  experience_years?: number;
  consultation_fee?: number;
  biography?: string;
  is_available: boolean;
  consultation_duration: number;
  specializations: Specialization[];
  department?: Department;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: number;
  name: string;
  description?: string;
  head_doctor_id?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Specialization {
  id: number;
  name: string;
  description?: string;
  created_at: string;
}

export interface DoctorSchedule {
  id: number;
  doctor_id: number;
  date?: string;
  day_of_week?: number;
  is_recurring: boolean;
  start_time: string;
  end_time: string;
  is_available: boolean;
  max_appointments: number;
  break_start_time?: string;
  break_end_time?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateDoctorRequest {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  date_of_birth?: string;
  gender?: 'male' | 'female' | 'other';
  address?: string;
  license_number: string;
  department_id: number;
  qualification?: string;
  experience_years?: number;
  consultation_fee?: number;
  biography?: string;
  consultation_duration?: number;
  specialization_ids?: number[];
}

export interface UpdateDoctorRequest {
  first_name?: string;
  last_name?: string;
  phone?: string;
  date_of_birth?: string;
  gender?: 'male' | 'female' | 'other';
  address?: string;
  license_number?: string;
  department_id?: number;
  qualification?: string;
  experience_years?: number;
  consultation_fee?: number;
  biography?: string;
  consultation_duration?: number;
  is_available?: boolean;
  specialization_ids?: number[];
}

export interface CreateScheduleRequest {
  date?: string;
  day_of_week?: number;
  is_recurring?: boolean;
  start_time: string;
  end_time: string;
  break_start_time?: string;
  break_end_time?: string;
  max_appointments?: number;
  is_available?: boolean;
}