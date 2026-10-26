import { Suspense } from 'react';
import { TemplateLibrary } from '../../components/templates';
export const metadata={title:'结构参考'};
export default function TemplatesPage(){return <Suspense fallback={<div className="page-state">正在加载模板库…</div>}><TemplateLibrary/></Suspense>;}
