import React from "react";
import Iframe from "react-iframe";

const IFrame = ({ record }) => (
  <div>
    <Iframe
      url={record.mlflowUri}
      width="100%"
      height="900"
      id="myId"
      className="myClassname"
      display="initial"
      position="relative"
    />
  </div>
);

export default IFrame;
