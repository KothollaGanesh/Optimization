export interface User {
  id: number;
  email: string;
  role: UserRole;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string;
  date_of_birth?: string;
  gender?: 'male' | 'female' | 'other';
  address?: string;
  is_active: boolean;
  email_verified: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export enum UserRole {
  ADMIN = 'admin',
  DOCTOR = 'doctor',
  PATIENT = 'patient',
  RECEPTIONIST = 'receptionist'
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  message: string;
  access_token: string;
  refresh_token: string;
  user: User;
  profile?: any;
}

export interface RegisterPatientRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  date_of_birth?: string;
  gender?: 'male' | 'female' | 'other';
  address?: string;
  blood_group?: string;
  allergies?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relation?: string;
  insurance_provider?: string;
  insurance_policy_number?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}