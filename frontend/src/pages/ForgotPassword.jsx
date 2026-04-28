import ForgotPasswordForm from "@/components/Auth/ForgotPasswordForm";
import MetaTags from "@/components/Common/MetaTags";

const ForgotPassword = () => {
  return (
    <>
      <MetaTags
        title="Forgot Your Password | TipZed"
        description="Reset your TipZed account password. Enter your email address and we'll send you a link to reset your password."
        keywords="forgot password, reset password, password recovery, TipZed"
      />
      <div className="bg-gradient-to-br from-green-50 via-white to-orange-50 min-h-screen py-8 md:py-12 px-4 flex flex-col justify-center">
        <div className="w-full max-w-md mx-auto backdrop-blur-xl bg-white/80 shadow-2xl rounded-2xl p-6 md:p-8 border border-white/40">
          {/* Header Section */}
          <div className="text-center mb-6">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900">
              Forgot Your Password?
            </h2>
            <p className="text-gray-500 text-sm mt-2">
              Enter your email and we'll send you a link to reset it
            </p>
          </div>

          {/* Form Component */}
          <ForgotPasswordForm />
        </div>
      </div>
    </>
  );
};

export default ForgotPassword;
