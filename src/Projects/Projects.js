import React, { Children } from 'react';
import { List, Datagrid, TextField, ReferenceField, SelectInput,
    EditButton, Edit, SimpleForm, ReferenceInput, TextInput, 
    Create, SimpleList, Responsive, Filter,
    Show, SimpleShowLayout, 
 } from 'react-admin';
import CardActions from '@material-ui/core/CardActions';
import Button from '@material-ui/core/Button';

import IFrame from './IFrame';


const ProjectTitle = ({ record }) => {
     return <span>Project {record ? `"${record.id}"` : ''}</span>;
};

const cardActionStyle = {
    zIndex: 2,
    display: 'inline-block',
    float: 'right',
};

const ProjectShowActions = ({ basePath, data, resource }) => (
    <CardActions style={cardActionStyle}>
        <EditButton basePath={basePath} record={data} />
        <Button color="primary" >Custom Action</Button>
    </CardActions>
);


export const ProjectShow = (props) => (
    <div>
        <Show 
            title={<ProjectTitle />} 
            {...props}>
            <SimpleShowLayout>
                <TextField source="id" />
                <TextField source="name" />
                <TextField source="status" />
                <TextField source="description" />
                <TextField source="mlflowUri" />
                {/* <ReferenceField label="Author" source="createdBy" reference="users">
                    <TextField source="name" />
                </ReferenceField> */}
                <TextField source="createdAt" />
                <IFrame {...props} />
            </SimpleShowLayout>
        </Show>
    </div>
);

const ProjectFilter = (props) => (
    <Filter {...props}>
        <TextInput label="Search" source="q" alwaysOn />
        <SelectInput optionText="name" />
        <TextField source="status" />
        {/* <ReferenceInput label="Author" source="userId" reference="users" allowEmpty>
            <SelectInput optionText="name" />
        </ReferenceInput> */}
    </Filter>
);




export const ProjectList = ({ ...props }) => {
    
    // console.log(props)
    
    return (
        <List  {...props}>
            <Datagrid rowClick="show"  {...props}>
                <TextField source="id" />
                <TextField source="name" />
                <TextField source="description" />
                <TextField source="status" />
                {/* <ReferenceField label="Author" source="createdBy" reference="users">
                    <TextField source="name" />
                </ReferenceField> */}
                <TextField source="createdAt" />
                {/* <ShowButton /> */}
                <EditButton />
            </Datagrid>
           
    </List>
    );
};

export const ProjectEdit = props => (
    <Edit title={<ProjectTitle />} {...props}>
        <SimpleForm>
            <TextField source="id" />
            <TextField source="name" />
            <TextField source="status" />
            <TextField source="description" />
            <TextField source="mlflowUri" />
            {/* <ReferenceField label="Author" source="createdBy" reference="users">
                <TextField source="name" />
            </ReferenceField> */}
            <TextField source="createdAt" />


        </SimpleForm> 
    </Edit>
);

export const ProjectCreate = props => (
    <Create {...props}>
        <SimpleForm>
            <TextField source="name" />
            <TextField source="status" />
            <TextField source="description" />
        </SimpleForm>
    </Create>
);