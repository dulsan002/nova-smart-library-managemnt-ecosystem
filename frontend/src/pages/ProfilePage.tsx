/**
 * ProfilePage — user profile with editable info, password change, and preferences.
 */

import { useQuery, useMutation } from '@apollo/client';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { useState } from 'react';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { ME } from '@/graphql/queries/auth';
import { UPDATE_PROFILE, CHANGE_PASSWORD } from '@/graphql/mutations/auth';
import { useAuthStore } from '@/stores/authStore';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { Tabs } from '@/components/ui/Tabs';
import { LoadingScreen } from '@/components/ui/Spinner';
import { extractGqlError } from '@/lib/utils';

const profileSchema = z.object({
  firstName: z.string().min(1, 'Required'),
  lastName: z.string().min(1, 'Required'),
});

const passwordSchema = z
  .object({
    oldPassword: z.string().min(1, 'Required'),
    newPassword: z.string().min(8, 'At least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.newPassword === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export default function ProfilePage() {
  useDocumentTitle('Profile');

  const { data, loading, refetch } = useQuery(ME);
  const user = data?.me;

  if (loading) return <LoadingScreen />;
  if (!user) return null;

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-nova-text">My Profile</h1>

      {/* Profile header */}
      <Card>
        <div className="flex items-center gap-4">
          <Avatar
            name={`${user.firstName} ${user.lastName}`}
            src={user.avatarUrl}
            size="xl"
          />
          <div>
            <h2 className="text-xl font-bold text-nova-text">
              {user.firstName} {user.lastName}
            </h2>
            <p className="text-sm text-nova-text-secondary">{user.email}</p>
            <div className="mt-2 flex items-center gap-2">
              <Badge variant="primary" size="sm">
                {user.role}
              </Badge>
              {user.isVerified && (
                <Badge variant="success" size="sm">
                  Verified
                </Badge>
              )}
            </div>
          </div>
        </div>
      </Card>

      <Tabs
        tabs={[
          {
            label: 'Edit Profile',
            content: <EditProfileForm user={user} onUpdate={refetch} />,
          },
          {
            label: 'Change Password',
            content: <ChangePasswordForm />,
          },
        ]}
      />
    </div>
  );
}

function EditProfileForm({ user, onUpdate }: { user: any; onUpdate: () => void }) {
  const setUser = useAuthStore((s) => s.setUser);

  type ProfileForm = z.infer<typeof profileSchema>;
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      firstName: user.firstName,
      lastName: user.lastName,
    },
  });

  const [updateProfile, { loading }] = useMutation(UPDATE_PROFILE, {
    onCompleted: (data) => {
      const updated = data?.updateProfile;
      if (updated) {
        setUser({
          id: updated.id,
          email: updated.email,
          firstName: updated.firstName,
          lastName: updated.lastName,
          role: updated.role,
          isVerified: updated.isVerified,
          avatarUrl: updated.avatarUrl,
        });
      }
      toast.success('Profile updated');
      onUpdate();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  return (
    <Card>
      <form
        onSubmit={handleSubmit((data) =>
          updateProfile({ variables: { input: data } }),
        )}
        className="space-y-5"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="First name"
            error={errors.firstName?.message}
            {...register('firstName')}
          />
          <Input
            label="Last name"
            error={errors.lastName?.message}
            {...register('lastName')}
          />
        </div>
        <Input label="Email" value={user.email} disabled />
        <div className="flex justify-end">
          <Button type="submit" isLoading={loading} disabled={!isDirty}>
            Save Changes
          </Button>
        </div>
      </form>
    </Card>
  );
}

function ChangePasswordForm() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(passwordSchema),
  });

  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [changePassword, { loading }] = useMutation(CHANGE_PASSWORD, {
    onCompleted: () => {
      toast.success('Password changed successfully');
      reset();
      setShowOldPassword(false);
      setShowNewPassword(false);
      setShowConfirmPassword(false);
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const passwordToggle = (show: boolean, setShow: (v: boolean) => void) => (
    <button
      type="button"
      onClick={() => setShow(!show)}
      className="rounded-md p-0.5 text-nova-text-muted transition-colors hover:text-nova-text focus:outline-none focus:ring-2 focus:ring-primary-500/40"
      tabIndex={-1}
      aria-label={show ? 'Hide password' : 'Show password'}
    >
      {show ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
    </button>
  );

  return (
    <Card>
      <form
        onSubmit={handleSubmit((data) =>
          changePassword({
            variables: {
              input: {
                oldPassword: data.oldPassword,
                newPassword: data.newPassword,
              },
            },
          }),
        )}
        className="space-y-5"
      >
        <Input
          label="Current password"
          type={showOldPassword ? 'text' : 'password'}
          error={errors.oldPassword?.message}
          rightIcon={passwordToggle(showOldPassword, setShowOldPassword)}
          {...register('oldPassword')}
        />
        <Input
          label="New password"
          type={showNewPassword ? 'text' : 'password'}
          error={errors.newPassword?.message}
          helperText="At least 8 characters"
          rightIcon={passwordToggle(showNewPassword, setShowNewPassword)}
          {...register('newPassword')}
        />
        <Input
          label="Confirm new password"
          type={showConfirmPassword ? 'text' : 'password'}
          error={errors.confirmPassword?.message}
          rightIcon={passwordToggle(showConfirmPassword, setShowConfirmPassword)}
          {...register('confirmPassword')}
        />
        <div className="flex justify-end">
          <Button type="submit" isLoading={loading}>
            Change Password
          </Button>
        </div>
      </form>
    </Card>
  );
}
