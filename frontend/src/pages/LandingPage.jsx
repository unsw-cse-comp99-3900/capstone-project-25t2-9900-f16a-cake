import React, { useEffect, useState } from "react";
import StaffLandingOld from "./StaffLandingOld";
import StaffLandingNew from "./StaffLandingNew";

function LandingPage() {
  const [layout, setLayout] = useState("old");

  // 获取布局配置
  const fetchLayoutConfig = async () => {
    try {
      const response = await fetch('/api/readconfig');
      const config = await response.json();
      setLayout(config.layout);
    } catch (error) {
      console.error('Failed to fetch layout config:', error);
    }
  };

  useEffect(() => {
    document.title = "Homepage";
    fetchLayoutConfig();
  }, []);

  // 根据布局配置渲染不同组件
  if (layout === "new") {
    return <StaffLandingNew />;
  } else {
    return <StaffLandingOld />;
  }
}

export default LandingPage; 