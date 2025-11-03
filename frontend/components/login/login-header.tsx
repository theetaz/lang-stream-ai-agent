import { CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot } from "lucide-react";

interface LoginHeaderProps {
  isLogin: boolean;
}

export function LoginHeader({ isLogin }: LoginHeaderProps) {
  return (
    <CardHeader className="space-y-4 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600">
        <Bot className="h-10 w-10 text-white" />
      </div>
      <div>
        <CardTitle className="text-2xl font-bold">Welcome to LangGraph AI</CardTitle>
        <CardDescription className="mt-2">
          {isLogin ? "Sign in to your account" : "Create a new account"}
        </CardDescription>
      </div>
    </CardHeader>
  );
}

