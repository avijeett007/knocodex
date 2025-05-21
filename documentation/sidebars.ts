import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // User Guide Sidebar
  userGuideSidebar: [
    {
      type: 'category',
      label: 'User Guide',
      items: [
        'user-guide/getting-started',
        'user-guide/installation',
        'user-guide/configuration',
        'user-guide/usage',
        'user-guide/issue-management',
        'user-guide/troubleshooting',
      ],
    },
  ],

  // Developer Guide Sidebar
  developerGuideSidebar: [
    {
      type: 'category',
      label: 'Developer Guide',
      items: [
        'developer-guide/architecture',
        'developer-guide/core-components',
        'developer-guide/api-reference',
        'developer-guide/contributing',
        'developer-guide/development-setup',
        'developer-guide/testing',
      ],
    },
  ],
};

export default sidebars;
