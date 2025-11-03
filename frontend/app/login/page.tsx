import { LoginContainer } from "@/components/login/login-container";
import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default async function LoginPage() {
  const cookieStore = await cookies();
  const backendToken = cookieStore.get("backend_access_token");

  if (backendToken) {
    redirect("/");
  }

  return <LoginContainer />;
}
