import React from "react";
import { DateField } from "react-admin";

const FormattedDateField = props => {
  const newProps = {
    ...props,
    record: {
      ...props.record,
      [props.source]: new Date(Number(props.record[props.source]))
    }
  };

  return <DateField {...newProps} />;
};

FormattedDateField.defaultProps = {
  addLabel: true
};

export default FormattedDateField;
