import { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import {
  verifyPasswordResetCode,
  confirmPasswordReset,
} from "firebase/auth";
import { auth } from "@/firebase";
import MetaTags from "@/components/Common/MetaTags";

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({ password: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [isValidCode, setIsValidCode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const oobCode = searchParams.get("oobCode");

  // Verify the reset code when component mounts
  useEffect(() => {
    const verifyCode = async () => {
      if (!oobCode) {
        setError("Invalid reset link. Please request a new password reset.");
        return;
      }

      try {
        const email = await verifyPasswordResetCode(auth, oobCode);
        setUserEmail(email);
        setIsValidCode(true);
      } catch (err) {
        console.error("Code verification error:", err);
        
        if (err.code === "auth/expired-action-code") {
          setError("This reset link has expired. Please request a new one.");
        } else if (err.code === "auth/invalid-action-code") {
          setError("Invalid reset link. Please request a new one.");
        } else {
          setError("Unable to verify reset link. Please try again.");
        }
      }
    };

    verifyCode();
  }, [oobCode]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validation
    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);

    try {
      await confirmPasswordReset(auth, oobCode, formData.password);
      setSuccess(true);
      setFormData({ password: "", confirmPassword: "" });
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate("/login", { 
          replace: true,
          state: { message: "Password reset successfully. Please log in." }
        });
      }, 3000);
    } catch (err) {
      console.error("Password reset error:", err);
      
      if (err.code === "auth/weak-password") {
        setError("Password is too weak. Please use a stronger password.");
      } else if (err.code === "auth/expired-action-code") {
        setError("Reset link has expired. Please request a new one.");
      } else if (err.code === "auth/invalid-action-code") {
        setError("Invalid reset link. Please request a new one.");
      } else {
        setError(err.message || "Failed to reset password. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <MetaTags
        title="Reset Your Password | TipZed"
        description="Reset your TipZed account password securely."
        keywords="reset password, password recovery, TipZed"
      />
      <div className="bg-gradient-to-br from-green-50 via-white to-orange-50 min-h-screen py-8 md:py-12 px-4 flex flex-col justify-center">
        <div className="w-full max-w-md mx-auto backdrop-blur-xl bg-white/80 shadow-2xl rounded-2xl p-6 md:p-8 border border-white/40">
          {/* Header Section */}
          <div className="text-center mb-6">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900">
              Reset Your Password
            </h2>
            {userEmail && (
              <p className="text-gray-500 text-sm mt-2">
                for {userEmail}
              </p>
            )}
          </div>

          {!isValidCode && !success ? (
            <div className="bg-yellow-50 text-yellow-700 text-sm p-4 rounded-lg border border-yellow-100 text-center">
              {error || "Verifying reset link..."}
            </div>
          ) : success ? (
            <div className="text-center space-y-4">
              <div className="bg-green-50 text-green-600 text-sm p-4 rounded-lg border border-green-100">
                Password reset successfully! Redirecting to login...
              </div>
              <Link
                to="/login"
                className="inline-block text-zed-orange font-medium hover:underline"
              >
                Go to Login →
              </Link>
            </div>
          ) : isValidCode ? (
            <form onSubmit={handleSubmit} className="space-y-6" noValidate={false}>
              {error && (
                <div
                  role="alert"
                  aria-live="polite"
                  className="bg-red-50 text-red-600 text-sm p-3 rounded-lg border border-red-100 transition-all"
                >
                  {error}
                </div>
              )}

              {/* New Password Input */}
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  New Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-zed-green focus:border-transparent outline-none transition-all"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-sm font-medium focus:outline-none"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
                <p className="text-gray-500 text-xs mt-1">
                  Must be at least 8 characters long
                </p>
              </div>

              {/* Confirm Password Input */}
              <div>
                <label
                  htmlFor="confirmPassword"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    required
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-zed-green focus:border-transparent outline-none transition-all"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-sm font-medium focus:outline-none"
                  >
                    {showConfirmPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 rounded-lg font-semibold text-white bg-zed-orange hover:bg-orange-600 transition shadow-md disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5 text-white"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    Resetting...
                  </span>
                ) : (
                  "Reset Password"
                )}
              </button>

              {/* Link back to login */}
              <div className="text-center text-sm text-gray-500">
                Remember your password?{" "}
                <Link
                  to="/login"
                  className="text-zed-orange font-medium hover:underline"
                >
                  Back to Login
                </Link>
              </div>
            </form>
          ) : null}
        </div>
      </div>
    </>
  );
};

export default ResetPassword;
