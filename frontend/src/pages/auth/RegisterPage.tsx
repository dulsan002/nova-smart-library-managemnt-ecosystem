/**
 * RegisterPage — Advanced multi-step registration with NIC verification.
 *
 * Steps:
 *   1. Personal Information (name, email, password, phone, DOB)
 *   2. NIC Verification (upload NIC photo, enter NIC number, AI verification)
 *   3. Review & Submit (summary of all details + verification result)
 *
 * The AI model performs OCR on the uploaded NIC card photo and verifies
 * that the entered details match the information on the card.
 */

import { useState, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useLazyQuery } from '@apollo/client';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import {
  EnvelopeIcon,
  LockClosedIcon,
  UserIcon,
  PhoneIcon,
  CalendarDaysIcon,
  IdentificationIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  CloudArrowUpIcon,
  ShieldCheckIcon,
  SparklesIcon,
  DocumentTextIcon,
  CameraIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';
import { CheckCircleIcon as CheckCircleSolid } from '@heroicons/react/24/solid';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { REGISTER_WITH_NIC, VERIFY_NIC } from '@/graphql/mutations/auth';
import { CHECK_EMAIL_AVAILABILITY } from '@/graphql/queries/auth';
import { extractGqlError } from '@/lib/utils';

/* ---------- Schemas ---------- */

const personalSchema = z
  .object({
    firstName: z.string().min(1, 'First name is required'),
    lastName: z.string().min(1, 'Last name is required'),
    email: z.string().email('Invalid email address'),
    phone: z.string().optional(),
    dateOfBirth: z.string().optional(),
    password: z
      .string()
      .min(8, 'At least 8 characters')
      .regex(/[A-Z]/, 'Needs an uppercase letter')
      .regex(/[0-9]/, 'Needs a number')
      .regex(/[^A-Za-z0-9]/, 'Needs a special character'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type PersonalValues = z.infer<typeof personalSchema>;

/* ---------- Types ---------- */

interface NICVerificationResult {
  success: boolean;
  isVerified: boolean;
  extractedName: string;
  extractedNicNumber: string;
  nameMatchScore: number;
  nicNumberMatch: boolean;
  ocrConfidence: number;
  documentType: string;
  message: string;
  status: 'APPROVED' | 'REJECTED' | 'MANUAL_REVIEW';
}

/* ---------- Step indicators ---------- */

const STEPS = [
  { label: 'Personal Info', icon: UserIcon },
  { label: 'NIC Verification', icon: IdentificationIcon },
  { label: 'Review & Submit', icon: ShieldCheckIcon },
];

function StepIndicator({
  current,
  steps,
}: {
  current: number;
  steps: typeof STEPS;
}) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {steps.map((step, i) => {
          const Icon = step.icon;
          const isComplete = i < current;
          const isCurrent = i === current;
          return (
            <div key={step.label} className="flex flex-1 items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-300 ${
                    isComplete
                      ? 'border-green-500 bg-green-500 text-white'
                      : isCurrent
                        ? 'border-primary-500 bg-primary-50 text-primary-600'
                        : 'border-gray-300 bg-white text-gray-400'
                  }`}
                >
                  {isComplete ? (
                    <CheckCircleSolid className="h-6 w-6" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                <span
                  className={`mt-2 text-xs font-medium ${
                    isCurrent
                      ? 'text-primary-600'
                      : isComplete
                        ? 'text-green-600'
                        : 'text-gray-400'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div
                  className={`mx-2 h-0.5 flex-1 transition-all duration-300 ${
                    isComplete ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ---------- Single Side NIC Uploader ---------- */

function NICSideUploader({
  side,
  label,
  onUploadComplete,
  uploadedUrl,
  isUploading,
  setIsUploading,
}: {
  side: 'front' | 'back';
  label: string;
  onUploadComplete: (path: string, url: string) => void;
  uploadedUrl: string | null;
  isUploading: boolean;
  setIsUploading: (v: boolean) => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.type.startsWith('image/')) {
        toast.error('Please upload an image file (JPG, PNG, or WebP)');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File too large. Maximum size is 10 MB.');
        return;
      }

      setIsUploading(true);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('type', `nic_${side}`);

      try {
        const resp = await fetch('/api/upload/verification/', {
          method: 'POST',
          body: formData,
        });
        const data = await resp.json();
        if (data.success) {
          onUploadComplete(data.path, data.url);
          toast.success(`${label} uploaded`);
        } else {
          toast.error(data.error || 'Upload failed');
        }
      } catch {
        toast.error('Upload failed. Please check your connection.');
      } finally {
        setIsUploading(false);
      }
    },
    [side, label, onUploadComplete, setIsUploading],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      if (e.dataTransfer.files?.[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile],
  );

  return (
    <div>
      {uploadedUrl ? (
        <div className="relative overflow-hidden rounded-xl border-2 border-green-300 bg-green-50 p-2">
          <img
            src={uploadedUrl}
            alt={`NIC ${side}`}
            className="mx-auto max-h-36 rounded-lg object-contain"
          />
          <div className="mt-2 flex items-center justify-center gap-1.5 text-xs text-green-700">
            <CheckCircleIcon className="h-4 w-4" />
            {label} uploaded
          </div>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="mx-auto mt-1 block text-xs text-primary-600 hover:underline"
          >
            Replace
          </button>
        </div>
      ) : (
        <div
          className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-5 transition-all ${
            dragActive
              ? 'border-primary-400 bg-primary-50'
              : 'border-gray-300 bg-gray-50 hover:border-primary-300 hover:bg-gray-100'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
        >
          {isUploading ? (
            <div className="flex flex-col items-center gap-2">
              <div className="h-8 w-8 animate-spin rounded-full border-3 border-primary-200 border-t-primary-600" />
              <p className="text-xs text-nova-text-secondary">Uploading…</p>
            </div>
          ) : (
            <>
              <CameraIcon className="h-8 w-8 text-primary-400" />
              <p className="mt-2 text-xs font-medium text-nova-text">
                {label}
              </p>
              <p className="mt-0.5 text-[10px] text-nova-text-muted">
                Drop or click to browse
              </p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="mt-2"
                leftIcon={<CloudArrowUpIcon className="h-3.5 w-3.5" />}
                onClick={() => fileInputRef.current?.click()}
              >
                Choose
              </Button>
            </>
          )}
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          if (e.target.files?.[0]) handleFile(e.target.files[0]);
        }}
      />
    </div>
  );
}

/* ---------- Verification Result Display ---------- */

function VerificationResultCard({ result }: { result: NICVerificationResult }) {
  const statusConfig = {
    APPROVED: {
      icon: CheckCircleIcon,
      bg: 'bg-green-50 border-green-200',
      iconColor: 'text-green-500',
      titleColor: 'text-green-800',
      title: 'Identity Verified',
    },
    MANUAL_REVIEW: {
      icon: ExclamationTriangleIcon,
      bg: 'bg-amber-50 border-amber-200',
      iconColor: 'text-amber-500',
      titleColor: 'text-amber-800',
      title: 'Manual Review Required',
    },
    REJECTED: {
      icon: XCircleIcon,
      bg: 'bg-red-50 border-red-200',
      iconColor: 'text-red-500',
      titleColor: 'text-red-800',
      title: 'Verification Failed',
    },
  };

  const config = statusConfig[result.status];
  const Icon = config.icon;

  return (
    <div className={`rounded-xl border-2 p-5 ${config.bg}`}>
      <div className="flex items-start gap-3">
        <Icon className={`h-7 w-7 flex-shrink-0 ${config.iconColor}`} />
        <div className="flex-1">
          <h4 className={`font-semibold ${config.titleColor}`}>
            {config.title}
          </h4>
          <p className="mt-1 text-sm text-gray-600">{result.message}</p>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-white/60 p-3">
              <p className="text-xs text-gray-500">Extracted Name</p>
              <p className="mt-0.5 text-sm font-medium text-gray-800">
                {result.extractedName || 'Not detected'}
              </p>
            </div>
            <div className="rounded-lg bg-white/60 p-3">
              <p className="text-xs text-gray-500">Extracted NIC Number</p>
              <p className="mt-0.5 text-sm font-medium text-gray-800">
                {result.extractedNicNumber || 'Not detected'}
              </p>
            </div>
            <div className="rounded-lg bg-white/60 p-3">
              <p className="text-xs text-gray-500">Name Match</p>
              <div className="mt-0.5 flex items-center gap-2">
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-200">
                  <div
                    className={`h-full rounded-full transition-all ${
                      result.nameMatchScore >= 0.65
                        ? 'bg-green-500'
                        : result.nameMatchScore >= 0.5
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                    }`}
                    style={{ width: `${result.nameMatchScore * 100}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-gray-600">
                  {Math.round(result.nameMatchScore * 100)}%
                </span>
              </div>
            </div>
            <div className="rounded-lg bg-white/60 p-3">
              <p className="text-xs text-gray-500">NIC Number Match</p>
              <p
                className={`mt-0.5 text-sm font-medium ${result.nicNumberMatch ? 'text-green-600' : 'text-red-600'}`}
              >
                {result.nicNumberMatch ? '✓ Matched' : '✗ Mismatch'}
              </p>
            </div>
            <div className="rounded-lg bg-white/60 p-3">
              <p className="text-xs text-gray-500">OCR Confidence</p>
              <div className="mt-0.5 flex items-center gap-2">
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-200">
                  <div
                    className={`h-full rounded-full transition-all ${
                      result.ocrConfidence >= 0.7
                        ? 'bg-green-500'
                        : result.ocrConfidence >= 0.5
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                    }`}
                    style={{ width: `${result.ocrConfidence * 100}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-gray-600">
                  {Math.round(result.ocrConfidence * 100)}%
                </span>
              </div>
            </div>
            <div className="rounded-lg bg-white/60 p-3">
              <p className="text-xs text-gray-500">Document Type</p>
              <p className="mt-0.5 text-sm font-medium text-gray-800">
                {result.documentType || 'Unknown'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ========== Main RegisterPage Component ========== */

export default function RegisterPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);

  /* Step 1 form */
  const {
    register: regField,
    handleSubmit: handleStep1Submit,
    formState: { errors: step1Errors },
    getValues: getPersonalValues,
    trigger: triggerStep1,
  } = useForm<PersonalValues>({
    resolver: zodResolver(personalSchema),
    mode: 'onBlur',
  });

  /* Step 2 state — front and back of NIC */
  const [nicNumber, setNicNumber] = useState('');
  const [nicFrontPath, setNicFrontPath] = useState('');
  const [nicFrontUrl, setNicFrontUrl] = useState<string | null>(null);
  const [nicBackPath, setNicBackPath] = useState('');
  const [nicBackUrl, setNicBackUrl] = useState<string | null>(null);
  const [isFrontUploading, setIsFrontUploading] = useState(false);
  const [isBackUploading, setIsBackUploading] = useState(false);
  const [verificationResult, setVerificationResult] =
    useState<NICVerificationResult | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  /* Mutations */
  const [verifyNICMut] = useMutation(VERIFY_NIC);
  const [registerMut, { loading: registering }] =
    useMutation(REGISTER_WITH_NIC);

  /* Email availability check */
  const [checkEmailQuery] = useLazyQuery(CHECK_EMAIL_AVAILABILITY);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [isCheckingEmail, setIsCheckingEmail] = useState(false);

  /* Password visibility toggles */
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  /* --- Step navigation --- */

  async function goToStep2() {
    const valid = await triggerStep1();
    if (!valid) return;

    // Check email availability before proceeding
    const email = getPersonalValues().email;
    setIsCheckingEmail(true);
    setEmailError(null);
    try {
      const { data } = await checkEmailQuery({ variables: { email } });
      if (data?.checkEmailAvailability === false) {
        setEmailError('An account with this email already exists.');
        toast.error('An account with this email already exists. Please use a different email or sign in.');
        setIsCheckingEmail(false);
        return;
      }
    } catch (err) {
      // If the check fails, allow proceeding (backend will catch it at registration)
      console.warn('Email availability check failed:', err);
    }
    setIsCheckingEmail(false);
    setStep(1);
  }

  function goToStep3() {
    if (!nicFrontPath) {
      toast.error('Please upload the front side of your NIC');
      return;
    }
    if (!nicBackPath) {
      toast.error('Please upload the back side of your NIC');
      return;
    }
    if (!nicNumber.trim()) {
      toast.error('Please enter your NIC number');
      return;
    }
    if (!verificationResult) {
      toast.error('Please verify your NIC first');
      return;
    }
    setStep(2);
  }

  /* --- NIC Upload handlers (front & back) --- */

  function handleFrontUpload(path: string, url: string) {
    setNicFrontPath(path);
    setNicFrontUrl(url);
    setVerificationResult(null);
  }

  function handleBackUpload(path: string, url: string) {
    setNicBackPath(path);
    setNicBackUrl(url);
    setVerificationResult(null);
  }

  /* --- NIC Verification --- */

  async function handleVerifyNIC() {
    if (!nicFrontPath) {
      toast.error('Please upload the front side of your NIC first');
      return;
    }
    if (!nicBackPath) {
      toast.error('Please upload the back side of your NIC');
      return;
    }
    if (!nicNumber.trim()) {
      toast.error('Please enter your NIC number');
      return;
    }

    const personal = getPersonalValues();
    const fullName = `${personal.firstName} ${personal.lastName}`;

    setIsVerifying(true);
    try {
      const { data } = await verifyNICMut({
        variables: {
          input: {
            nicFrontImagePath: nicFrontPath,
            nicBackImagePath: nicBackPath,
            fullName,
            nicNumber: nicNumber.trim(),
          },
        },
      });

      const result = data.verifyNic as NICVerificationResult;
      setVerificationResult(result);

      if (result.status === 'APPROVED') {
        toast.success('NIC verified successfully!');
      } else if (result.status === 'MANUAL_REVIEW') {
        toast('NIC will need manual review. You can still proceed.', {
          icon: '⚠️',
        });
      } else {
        toast.error('NIC verification failed. Try with a clearer photo.');
      }
    } catch (err) {
      toast.error(extractGqlError(err));
    } finally {
      setIsVerifying(false);
    }
  }

  /* --- Final Registration --- */

  async function handleFinalSubmit() {
    const personal = getPersonalValues();

    try {
      const { data } = await registerMut({
        variables: {
          input: {
            email: personal.email,
            password: personal.password,
            firstName: personal.firstName,
            lastName: personal.lastName,
            phoneNumber: personal.phone || undefined,
            dateOfBirth: personal.dateOfBirth || undefined,
            nicNumber: nicNumber.trim(),
            nicFrontImagePath: nicFrontPath,
            nicBackImagePath: nicBackPath || undefined,
          },
        },
      });

      const verStatus = data.registerWithNic.verification.status as string;

      if (verStatus === 'APPROVED') {
        toast.success(
          'Account created and verified! You can now sign in.',
        );
      } else if (verStatus === 'MANUAL_REVIEW') {
        toast.success(
          'Account created! Your NIC is under review. We will notify you once approved.',
        );
      } else {
        toast(
          'Account created but NIC verification failed. An administrator will review your application.',
          { icon: 'ℹ️' },
        );
      }
      navigate('/login');
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  }

  /* --- Render --- */

  const personal = step > 0 ? getPersonalValues() : null;

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl font-bold text-nova-text">Create an account</h2>
      <p className="mt-1 text-sm text-nova-text-secondary">
        Join the NovaLib knowledge ecosystem
      </p>

      <StepIndicator current={step} steps={STEPS} />

      {/* ================================ */}
      {/* STEP 1 — Personal Information    */}
      {/* ================================ */}
      {step === 0 && (
        <form
          onSubmit={handleStep1Submit(() => goToStep2())}
          className="space-y-4"
        >
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First name"
              placeholder="Jane"
              autoComplete="given-name"
              leftIcon={<UserIcon className="h-5 w-5" />}
              error={step1Errors.firstName?.message}
              {...regField('firstName')}
            />
            <Input
              label="Last name"
              placeholder="Doe"
              autoComplete="family-name"
              leftIcon={<UserIcon className="h-5 w-5" />}
              error={step1Errors.lastName?.message}
              {...regField('lastName')}
            />
          </div>

          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            leftIcon={<EnvelopeIcon className="h-5 w-5" />}
            error={step1Errors.email?.message || emailError || undefined}
            {...regField('email', {
              onChange: () => {
                if (emailError) setEmailError(null);
              },
            })}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Phone number"
              type="tel"
              placeholder="+94 77 123 4567"
              autoComplete="tel"
              leftIcon={<PhoneIcon className="h-5 w-5" />}
              {...regField('phone')}
            />
            <Input
              label="Date of birth"
              type="date"
              autoComplete="bday"
              leftIcon={<CalendarDaysIcon className="h-5 w-5" />}
              {...regField('dateOfBirth')}
            />
          </div>

          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder={showPassword ? 'Enter your password' : '••••••••'}
            autoComplete="new-password"
            leftIcon={<LockClosedIcon className="h-5 w-5" />}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="rounded-md p-0.5 text-nova-text-muted transition-colors hover:text-nova-text focus:outline-none focus:ring-2 focus:ring-primary-500/40"
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            }
            error={step1Errors.password?.message}
            helperText="Min 8 chars, uppercase, number, and special character"
            {...regField('password')}
          />

          <Input
            label="Confirm password"
            type={showConfirmPassword ? 'text' : 'password'}
            placeholder={showConfirmPassword ? 'Confirm your password' : '••••••••'}
            autoComplete="new-password"
            leftIcon={<LockClosedIcon className="h-5 w-5" />}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowConfirmPassword((v) => !v)}
                className="rounded-md p-0.5 text-nova-text-muted transition-colors hover:text-nova-text focus:outline-none focus:ring-2 focus:ring-primary-500/40"
                tabIndex={-1}
                aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
              >
                {showConfirmPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            }
            error={step1Errors.confirmPassword?.message}
            {...regField('confirmPassword')}
          />

          <Button type="submit" fullWidth className="mt-2" disabled={isCheckingEmail}>
            {isCheckingEmail ? (
              <>
                <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Checking availability...
              </>
            ) : (
              <>
                Continue to NIC Verification
                <ArrowRightIcon className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>

          <p className="mt-4 text-center text-sm text-nova-text-secondary">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-semibold text-primary-600 hover:text-primary-500"
            >
              Sign in
            </Link>
          </p>
        </form>
      )}

      {/* ================================ */}
      {/* STEP 2 — NIC Verification        */}
      {/* ================================ */}
      {step === 1 && (
        <div className="space-y-5">
          <div className="rounded-xl bg-gradient-to-r from-primary-50 to-accent-50 p-4">
            <div className="flex items-center gap-3">
              <SparklesIcon className="h-6 w-6 text-primary-600" />
              <div>
                <h3 className="text-sm font-semibold text-primary-800">
                  AI-Powered Identity Verification
                </h3>
                <p className="text-xs text-primary-600">
                  Upload both sides of your NIC card. Our AI will extract and
                  verify your details instantly.
                </p>
              </div>
            </div>
          </div>

          {/* NIC front & back uploaders */}
          <div>
            <label className="mb-2 block text-sm font-medium text-nova-text">
              NIC Card Photos <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <NICSideUploader
                side="front"
                label="Front Side"
                onUploadComplete={handleFrontUpload}
                uploadedUrl={nicFrontUrl}
                isUploading={isFrontUploading}
                setIsUploading={setIsFrontUploading}
              />
              <NICSideUploader
                side="back"
                label="Back Side"
                onUploadComplete={handleBackUpload}
                uploadedUrl={nicBackUrl}
                isUploading={isBackUploading}
                setIsUploading={setIsBackUploading}
              />
            </div>
          </div>

          {/* Tips */}
          <div className="rounded-lg bg-blue-50 p-3">
            <div className="flex gap-2">
              <DocumentTextIcon className="h-5 w-5 flex-shrink-0 text-blue-500" />
              <div className="text-xs text-blue-700">
                <p className="font-medium">Tips for best results:</p>
                <ul className="mt-1 list-inside list-disc space-y-0.5">
                  <li>Photograph both the front and back of your NIC</li>
                  <li>Ensure all text is readable and not blurry</li>
                  <li>Avoid glare, shadows, and cropped edges</li>
                  <li>Include the full card in the frame</li>
                </ul>
              </div>
            </div>
          </div>

          {/* NIC number input */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-nova-text">
              NIC Number <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <IdentificationIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={nicNumber}
                onChange={(e) => {
                  setNicNumber(e.target.value);
                  setVerificationResult(null);
                }}
                placeholder="e.g. 200012345678 or 901234567V"
                className="block w-full rounded-lg border border-gray-300 bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-200"
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Enter the NIC number exactly as it appears on your card
            </p>
          </div>

          {/* Verify button */}
          <Button
            type="button"
            fullWidth
            variant="outline"
            onClick={handleVerifyNIC}
            isLoading={isVerifying}
            disabled={!nicFrontPath || !nicBackPath || !nicNumber.trim()}
          >
            <ShieldCheckIcon className="mr-2 h-5 w-5" />
            Verify NIC with AI
          </Button>

          {/* Verification result */}
          {verificationResult && (
            <VerificationResultCard result={verificationResult} />
          )}

          {/* Navigation */}
          <div className="flex gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => setStep(0)}
              className="flex-1"
            >
              <ArrowLeftIcon className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button
              type="button"
              onClick={goToStep3}
              disabled={!verificationResult}
              className="flex-1"
            >
              Review Details
              <ArrowRightIcon className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* ================================ */}
      {/* STEP 3 — Review & Submit         */}
      {/* ================================ */}
      {step === 2 && personal && verificationResult && (
        <div className="space-y-5">
          {/* Personal info summary */}
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-800">
              <UserIcon className="h-5 w-5 text-primary-500" />
              Personal Information
            </h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-500">Name</span>
                <p className="font-medium text-gray-800">
                  {personal.firstName} {personal.lastName}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Email</span>
                <p className="font-medium text-gray-800">{personal.email}</p>
              </div>
              {personal.phone && (
                <div>
                  <span className="text-gray-500">Phone</span>
                  <p className="font-medium text-gray-800">{personal.phone}</p>
                </div>
              )}
              {personal.dateOfBirth && (
                <div>
                  <span className="text-gray-500">Date of Birth</span>
                  <p className="font-medium text-gray-800">
                    {personal.dateOfBirth}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* NIC verification summary */}
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-800">
              <IdentificationIcon className="h-5 w-5 text-primary-500" />
              NIC Verification
            </h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-500">NIC Number</span>
                <p className="font-medium text-gray-800">{nicNumber}</p>
              </div>
              <div>
                <span className="text-gray-500">Verification Status</span>
                <p
                  className={`font-medium ${
                    verificationResult.status === 'APPROVED'
                      ? 'text-green-600'
                      : verificationResult.status === 'MANUAL_REVIEW'
                        ? 'text-amber-600'
                        : 'text-red-600'
                  }`}
                >
                  {verificationResult.status === 'APPROVED'
                    ? '✓ Verified'
                    : verificationResult.status === 'MANUAL_REVIEW'
                      ? '⏳ Pending Review'
                      : '✗ Failed'}
                </p>
              </div>
            </div>
            {(nicFrontUrl || nicBackUrl) && (
              <div className="mt-3 flex gap-3">
                {nicFrontUrl && (
                  <div className="text-center">
                    <img
                      src={nicFrontUrl}
                      alt="NIC Front"
                      className="max-h-20 rounded-lg border border-gray-200 object-contain"
                    />
                    <p className="mt-1 text-[10px] text-gray-400">Front</p>
                  </div>
                )}
                {nicBackUrl && (
                  <div className="text-center">
                    <img
                      src={nicBackUrl}
                      alt="NIC Back"
                      className="max-h-20 rounded-lg border border-gray-200 object-contain"
                    />
                    <p className="mt-1 text-[10px] text-gray-400">Back</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Status Banner */}
          {verificationResult.status === 'APPROVED' && (
            <div className="flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4">
              <CheckCircleIcon className="h-6 w-6 flex-shrink-0 text-green-500" />
              <p className="text-sm text-green-800">
                Your identity has been verified. Your account will be activated
                immediately upon registration.
              </p>
            </div>
          )}

          {verificationResult.status === 'MANUAL_REVIEW' && (
            <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <ExclamationTriangleIcon className="h-6 w-6 flex-shrink-0 text-amber-500" />
              <p className="text-sm text-amber-800">
                Your NIC could not be fully verified. An administrator will
                review your application. You&apos;ll be able to sign in once
                approved.
              </p>
            </div>
          )}

          {verificationResult.status === 'REJECTED' && (
            <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
              <XCircleIcon className="h-6 w-6 flex-shrink-0 text-red-500" />
              <p className="text-sm text-red-800">
                NIC verification failed. You can still register, but your
                account will require manual approval before activation.
              </p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => setStep(1)}
              className="flex-1"
            >
              <ArrowLeftIcon className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button
              type="button"
              onClick={handleFinalSubmit}
              isLoading={registering}
              className="flex-1"
            >
              <ShieldCheckIcon className="mr-2 h-5 w-5" />
              Create Account
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
