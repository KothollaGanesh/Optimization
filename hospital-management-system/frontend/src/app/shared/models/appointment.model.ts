import { Patient } from './patient.model';
import { Doctor } from './doctor.model';

export interface Appointment {
  id: number;
  appointment_number: string;
  patient_id: number;
  doctor_id: number;
  service_id?: number;
  appointment_date: string;
  appointment_time: string;
  appointment_datetime: string;
  duration_minutes: number;
  appointment_type: AppointmentType;
  status: AppointmentStatus;
  priority: 'low' | 'normal' | 'high' | 'emergency';
  chief_complaint?: string;
  notes?: string;
  created_by_user_id?: number;
  checked_in_at?: string;
  checked_out_at?: string;
  follow_up_appointment_id?: number;
  parent_appointment_id?: number;
  cancellation_reason?: string;
  cancelled_by_user_id?: number;
  cancelled_at?: string;
  patient?: Patient;
  doctor?: Doctor;
  service?: Service;
  created_at: string;
  updated_at: string;
}

export enum AppointmentType {
  CONSULTATION = 'consultation',
  FOLLOW_UP = 'follow_up',
  EMERGENCY = 'emergency',
  ROUTINE_CHECKUP = 'routine_checkup',
  SPECIALIST = 'specialist'
}

export enum AppointmentStatus {
  SCHEDULED = 'scheduled',
  CONFIRMED = 'confirmed',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show',
  RESCHEDULED = 'rescheduled'
}

export interface Service {
  id: number;
  name: string;
  description?: string;
  service_code: string;
  base_price: number;
  insurance_price?: number;
  duration_minutes: number;
  formatted_duration: string;
  category?: string;
  subcategory?: string;
  department_id: number;
  is_active: boolean;
  requires_appointment: boolean;
  is_emergency_service: boolean;
  requires_referral: boolean;
  preparation_instructions?: string;
  department?: any;
  created_at: string;
  updated_at: string;
}

export interface CreateAppointmentRequest {
  patient_id: number;
  doctor_id: number;
  service_id?: number;
  appointment_date: string;
  appointment_time: string;
  appointment_type?: AppointmentType;
  chief_complaint?: string;
  notes?: string;
  priority?: 'low' | 'normal' | 'high' | 'emergency';
}

export interface UpdateAppointmentRequest {
  appointment_date?: string;
  appointment_time?: string;
  appointment_type?: AppointmentType;
  status?: AppointmentStatus;
  chief_complaint?: string;
  notes?: string;
  priority?: 'low' | 'normal' | 'high' | 'emergency';
}

export interface CancelAppointmentRequest {
  reason: string;
}

export interface AvailableSlot {
  time: string;
  available: boolean;
}