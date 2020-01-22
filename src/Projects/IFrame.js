import React from 'react'
import Iframe from 'react-iframe'

// https://www.npmjs.com/package/react-iframe


const IFrame = ({ record })  => (
   
    <div>
        <Iframe 
            url={ record.mlflowUri }
            width="100%"
            height="900"s
            id="myId"
            className="myClassname"
            display="initial"
            position="relative"
            />
    </div>
);

export default IFrame;