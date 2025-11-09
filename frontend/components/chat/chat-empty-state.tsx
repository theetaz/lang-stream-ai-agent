import { Sparkles } from "lucide-react";

export function ChatEmptyState() {
  return (
    <div className="flex flex-1 items-center justify-center p-4">
      <div className="max-w-2xl text-center space-y-6">
        <div className="flex justify-center">
          <div className="rounded-full bg-gradient-to-br from-blue-600 to-purple-600 p-4">
            <Sparkles className="h-12 w-12 text-white" />
          </div>
        </div>
        <div className="space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">What can I help with?</h2>
        </div>
      </div>
    </div>
  );
}

