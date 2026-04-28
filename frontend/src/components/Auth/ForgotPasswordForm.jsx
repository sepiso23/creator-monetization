import { useState } from "react";
import { Link } from "react-router-dom";
import { sendPasswordResetEmail } from "firebase/auth";
import { auth } from "@/firebase";

const ForgotPasswordForm = () => {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }

    setIsLoading(true);

    try {
      await sendPasswordResetEmail(auth, email.trim());
      setSuccess(true);
      setEmail("");
    } catch (err) {
      console.error("Password reset error:", err);
      
      // Handle specific Firebase errors
      if (err.code === "auth/user-not-found") {
        setError("No account found with this email address.");
      } else if (err.code === "auth/invalid-email") {
        setError("Please enter a valid email address.");
      } else if (err.code === "auth/too-many-requests") {
        setError("Too many reset attempts. Please try again later.");
      } else {
        setError(err.message || "Failed to send reset email. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
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

      {success && (
        <div
          role="alert"
          aria-live="polite"
          className="bg-green-50 text-green-600 text-sm p-3 rounded-lg border border-green-100 transition-all"
        >
          Password reset email sent! Check your inbox for instructions.
        </div>
      )}

      {/* Email Input */}
      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Email Address
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-zed-green focus:border-transparent outline-none transition-all"
          placeholder="you@example.com"
          disabled={isLoading || success}
        />
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || success}
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
            Sending...
          </span>
        ) : success ? (
          "Email Sent!"
        ) : (
          "Send Reset Link"
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
  );
};

export default ForgotPasswordForm;
