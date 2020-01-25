import React from "react";
import { DateField } from "react-admin";

const FormattedDateField = props => {
  const { innerProp: innerPropValue = "" } = props;
  let newProps = {};

  if (innerPropValue) {
    newProps = {
      ...props,
      source: `${innerPropValue}.${props.source}`,
      record: {
        ...props.record,
        [innerPropValue]: {
          ...props.record[innerPropValue],
          [props.source]: new Date(
            Number(props.record[innerPropValue][props.source])
          )
        }
      }
    };
  } else {
    newProps = {
      ...props,
      record: {
        ...props.record,
        [props.source]: new Date(Number(props.record[props.source]))
      }
    };
  }

  const { innerProp, ...restProps } = newProps;

  return <DateField {...restProps} />;
};

FormattedDateField.defaultProps = {
  addLabel: true
};

export default FormattedDateField;
