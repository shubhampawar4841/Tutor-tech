'use client';

import { useState } from 'react';
import { Lightbulb } from 'lucide-react';

export default function IdeaGenPage() {
  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="px-4 sm:px-0">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
              IdeaGen
            </h1>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Generate research ideas from your notebooks
            </p>
          </div>

          <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-12 text-center">
            <Lightbulb className="mx-auto h-12 w-12 text-zinc-400 mb-4" />
            <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-50 mb-2">
              Coming Soon
            </h3>
            <p className="text-zinc-500 dark:text-zinc-400">
              This feature will be available soon.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


