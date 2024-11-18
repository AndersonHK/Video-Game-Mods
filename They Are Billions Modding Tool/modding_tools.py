#Dependencies
import xml.etree.ElementTree as ET
from xml.dom import minidom

#Loading Data File
def parse_simple(elem):
    """Parse <Simple> element, preserving special XML characters and handling numeric values."""
    value = elem.attrib.get('value')
    
    if value is not None:
        # Check if the value can be converted to an integer
        try:
            return int(value)
        except ValueError:
            # If it's not an integer, check if it's a float (or leave as string)
            try:
                return float(value) if '.' in value else value
            except ValueError:
                return value.replace('\n', '&#xA;')  # Preserve special XML characters like &#xA;
    
    return value

def parse_complex(elem):
    """Parse <Complex> element into a dictionary."""
    result = {}
    for child in elem:
        if child.tag == "Properties":
            result.update(parse_properties(child))
    return result

def parse_dictionary(elem):
    """Parse <Dictionary> element."""
    result = {}
    for item in elem.find('Items'):
        key_elem = item.find('Simple')
        key = parse_simple(key_elem)
        value_elem = item.findall('Simple')

        if len(value_elem) == 2:
            value = parse_simple(value_elem[1])
        else:
            complex_elem = item.find('Complex')
            if complex_elem is not None:
                value = parse_complex(complex_elem)
            else:
                array_elem = item.find('SingleArray')
                if array_elem is not None:
                    value = parse_array(array_elem)
                else:
                    value = None

        result[key] = value
    return result

def parse_array(elem):
    """Parse <SingleArray> element into a list."""
    items = elem.find('Items')
    result = []
    for item in items:
        value = parse_simple(item)
        
        # Only apply string replacement if the value is a string
        if value is not None and isinstance(value, str):
            value = value.replace('\n', '&#xA;')
        
        result.append(value)
    
    return result


def parse_properties(elem):
    """Parse <Properties> element, which contains dictionaries and simple elements."""
    result = {}
    for prop in elem:
        if prop.tag == "Dictionary":
            name = prop.get('name')
            result[name] = parse_dictionary(prop)
        elif prop.tag == "Simple":
            result[prop.get('name')] = parse_simple(prop)
    return result

def load_dat_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    result = parse_complex(root)
    return result

#Saving Data File
def determine_value_type(values):
    """Determine the appropriate valueType based on the content of the dictionary."""
    #print(f"Determining valueType for values: {values}")  # Debugging print statement
    
    # If all values are integers
    if all(isinstance(v, int) for v in values):
        return "System.Int32, mscorlib"
    
    # If values are lists of mixed types (strings, None, and numbers)
    elif all(isinstance(v, list) and all(isinstance(i, (str, int, type(None))) for i in v) for v in values):
        return "System.String[], mscorlib"
    
    # If all values are strings
    elif all(isinstance(v, str) for v in values):
        return "System.String, mscorlib"
    
    else:
        # Default to string if mixed or unknown types
        return "System.String, mscorlib"

def format_complex_item(data, indent=0):
    indent_str = ' ' * indent  # Use 2-space indentation
    formatted = f'{indent_str}<Complex>\n'
    formatted += f'{indent_str}  <Properties>\n'  # Add Properties after Complex
    for key, value in data.items():
        if isinstance(value, dict):
            if key == 'Tables':  # Manually set the type for the 'Tables' dictionary
                formatted += f'{indent_str}    <Dictionary name="{key}" keyType="System.String, mscorlib" valueType="DXVision.DXTable, DXVision">\n'
                formatted += format_dict(value, indent + 6)  # Manually add indentation as per your fix
                formatted += f'{indent_str}    </Dictionary>\n'
            elif key in ['Cols', 'Rows']:  # Handle Cols and Rows as dictionaries
                # Dynamically determine the valueType for Cols and Rows
                value_type = determine_value_type(value.values())
                formatted += f'{indent_str}    <Dictionary name="{key}" keyType="System.String, mscorlib" valueType="{value_type}">\n'
                formatted += format_dict(value, indent + 6)  # Use the corrected indentation logic
                formatted += f'{indent_str}    </Dictionary>\n'
            else:
                formatted += f'{indent_str}    <Complex>\n'
                formatted += f'{indent_str}      <Properties>\n'
                formatted += format_dict(value, indent + 4)
                formatted += f'{indent_str}      </Properties>\n'
                formatted += f'{indent_str}    </Complex>\n'
        elif isinstance(value, list):
            # Handle arrays with <SingleArray>
            formatted += f'{indent_str}    <SingleArray elementType="System.String, mscorlib">\n'
            formatted += f'{indent_str}      <Items>\n'
            for item in value:
                # Debugging: Print item before formatting
                print(f'Item before formatting: {item}')  # <-- Add this line to debug each item
                
                if item is None:
                    formatted += f'{indent_str}        <Null />\n'
                else:
                    # Preserve any encoded special characters like &#xA;
                    item = item.replace('\n', '&#xA;') if isinstance(item, str) else item
                    formatted += f'{indent_str}        <Simple value="{item}" />\n'
            formatted += f'{indent_str}      </Items>\n'
            formatted += f'{indent_str}    </SingleArray>\n'
        else:
            if key == "Name":
                formatted += f'{indent_str}    <Simple name="{key}" value="{value}" />\n'
            else:
                # Debugging: Print value before formatting
                print(f'Value before formatting: {value}')  # <-- Add this line to debug values
                
                formatted += f'{indent_str}    <Simple value="{key}" />\n'
                if value is None:
                    formatted += f'{indent_str}    <Null />\n'
                else:
                    # Preserve &#xA; as is in the string
                    value = value.replace('\n', '&#xA;') if isinstance(value, str) else value
                    formatted += f'{indent_str}    <Simple value="{value}" />\n'
    formatted += f'{indent_str}  </Properties>\n'
    formatted += f'{indent_str}</Complex>\n'
    return formatted



def format_dict(data, indent=0):
    indent_str = ' ' * indent  # Use 2-space indentation
    formatted = f'{indent_str}<Items>\n'
    for key, value in data.items():
        formatted += f'{indent_str}  <Item>\n'
        if isinstance(value, dict):
            if key in ['Cols', 'Rows']:  # Handle dictionaries with dynamic valueType
                #print(f"Processing dictionary key '{key}' with values: {value.values()}") 
                value_type = determine_value_type(value.values())  # Determine the valueType dynamically
                formatted += f'{indent_str}    <Dictionary name="{key}" keyType="System.String, mscorlib" valueType="{value_type}">\n'
                formatted += format_dict(value, indent + 6)
                formatted += f'{indent_str}    </Dictionary>\n'
            else:
                formatted += f'{indent_str}    <Simple value="{key}" />\n'
                formatted += format_complex_item(value, indent + 4)
        elif isinstance(value, list):
            formatted += f'{indent_str}    <Simple value="{key}" />\n'
            formatted += f'{indent_str}    <SingleArray elementType="System.String, mscorlib">\n'
            formatted += f'{indent_str}      <Items>\n'
            for item in value:
                if item is None:
                    formatted += f'{indent_str}        <Null />\n'
                else:
                    formatted += f'{indent_str}        <Simple value="{item}" />\n'
            formatted += f'{indent_str}      </Items>\n'
            formatted += f'{indent_str}    </SingleArray>\n'
        else:
            formatted += f'{indent_str}    <Simple value="{key}" />\n'
            if value is None:
                formatted += f'{indent_str}    <Null />\n'
            else:
                formatted += f'{indent_str}    <Simple value="{value}" />\n'
        formatted += f'{indent_str}  </Item>\n'
    formatted += f'{indent_str}</Items>\n'
    return formatted

def save_custom_dat_file(save_file_path, data_dict):
    """Save the structured dictionary to a .dat file with correct format and indentation."""
    # Start the root of the file with <Complex>
    output = '<Complex name="Root" type="DXVision.DXTableManager, DXVision">\n  <Properties>\n'

    # Output the Tables section (root of the file)
    tables_data = data_dict.get('Tables', {})  # Safely get Tables data
    output += '    <Dictionary name="Tables" keyType="System.String, mscorlib" valueType="DXVision.DXTable, DXVision">\n'
    output += format_dict(tables_data, indent=6)  # Properly indent contents inside Tables
    output += '    </Dictionary>\n'

    # Close the Properties and Complex root tag
    output += '  </Properties>\n</Complex>\n'

    # Write to the file with UTF-8 BOM
    with open(save_file_path, 'w', encoding='utf-8-sig') as f:
        f.write(output)

#Editing Data File
class Table:
    """A class that dynamically handles both rows and columns access."""
    def __init__(self, name, cols, rows):
        self.name = name
        self.cols = cols  # Dictionary of column names and indices
        self.rows = rows  # Dictionary of row data

        # Perform a collision check between rows and columns
        self.check_for_collisions()

    def check_for_collisions(self):
        """Check for key collisions between rows and columns."""
        common_keys = set(self.rows.keys()) & set(self.cols.keys())
        if common_keys:
            print(f"Warning: Collision detected in table '{self.name}' for keys: {common_keys}")

    def get_column_index(self, column_name):
        """Get the index of a column based on its name."""
        if column_name in self.cols:
            return self.cols[column_name]
        else:
            raise AttributeError(f"Column '{column_name}' not found in table '{self.name}'.")

    def __getattr__(self, key):
        """Dynamically access a row or a column."""
        # First, check if it's a row key
        if key in self.rows:
            # Return a dynamic row accessor if the key matches a row
            return Row(self, key)
        # Then check if it's a column key
        elif key in self.cols:
            return self.cols[key]
        else:
            raise AttributeError(f"'{self.name}' table has no attribute '{key}'.")

    def __setattr__(self, key, value):
        """Dynamically set a value to a column or row."""
        if key in ['name', 'cols', 'rows']:  # Let the internal attributes be set normally
            super().__setattr__(key, value)
        elif key in self.rows:  # If it's a row key
            self.rows[key] = value
        elif key in self.cols:  # If it's a column key, treat it as a row value
            raise AttributeError(f"Cannot modify the column directly. Modify row data.")
        else:
            raise AttributeError(f"'{self.name}' table has no attribute '{key}'.")

    def __dir__(self):
        """Return a list of available attributes (row keys and column names)."""
        # Return a combined list of rows and columns for auto-completion
        return list(self.rows.keys()) + list(self.cols.keys())

    def __iter__(self):
        """Allow iteration over the rows."""
        for row_key in self.rows:
            yield Row(self, row_key)

    def __repr__(self):
        return f"<Table: {self.name}, Columns: {len(self.cols)}, Rows: {len(self.rows)}>"


class Row:
    """A class representing a single row in the table."""
    def __init__(self, table, row_key):
        self.table = table
        self.row_key = row_key

    def __getattr__(self, column_name):
        """Access a specific column in the row."""
        col_index = self.table.get_column_index(column_name)
        return self.table.rows[self.row_key][col_index]

    def __setattr__(self, column_name, new_value):
        """Set a specific column value in the row."""
        if column_name in ['table', 'row_key']:
            # Allow setting internal attributes
            super().__setattr__(column_name, new_value)
        else:
            col_index = self.table.get_column_index(column_name)
            self.table.rows[self.row_key][col_index] = new_value

    def __dir__(self):
        """Return a list of available columns for this row."""
        # Return the columns available for this particular row
        return list(self.table.cols.keys())

    def __repr__(self):
        return f"<Row: {self.row_key}>"


def create_table_classes(data_dict):
    """Dynamically create table instances for each table in data_dict['Tables']."""
    tables = data_dict.get('Tables', {})
    table_instances = {}

    for table_name, table_data in tables.items():
        cols = table_data.get('Cols', {})
        rows = table_data.get('Rows', {})

        # Dynamically create a table instance for each table
        table_instance = Table(name=table_name, cols=cols, rows=rows)
        table_instances[table_name] = table_instance

    return table_instances

#Float separator overwrite
def cfloat(value):
    """Convert a string with a comma to a float for comparison purposes."""
    try:
        # Replace comma with dot to convert string to float
        value_str = str(value).replace(',', '.')
        return float(value_str)
    except ValueError:
        return None  # Return None if conversion fails

def efloat(value, expression):
    """Convert string with comma to float, apply expression, and convert back to string.
       Keep whole numbers as integers, otherwise format with commas."""
    try:
        # Convert to float for calculation
        float_value = cfloat(value)
        if float_value is None:
            return value  # Return the original value if conversion fails
        
        # Apply the expression (e.g., multiplication)
        result_value = expression(float_value)
        
        # If the result is a whole number, return it as an integer string
        if result_value.is_integer():
            return str(int(result_value))
        else:
            # Otherwise, format with commas (e.g., "6,5")
            return f"{result_value}".replace('.', ',')
    except ValueError:
        return value  # Return original value if any error occurs