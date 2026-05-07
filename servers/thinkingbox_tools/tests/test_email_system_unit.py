import pytest

from thinkingbox_tools.toolslib.email_system import (
    Contact,
    EmailSystem,
    EmailSystemError,
)


def test_email_system_init():
    """Test EmailSystem initialization"""
    system = EmailSystem()
    assert isinstance(system._state, dict)
    assert system._state == {}
    assert system.default_user is None
    assert system.effects == []


def test_email_system_initialize():
    """Test EmailSystem initialization with config"""
    system = EmailSystem()
    config = {"users": {"alice@example.com": {}}}
    system.initialize(config)
    assert "alice@example.com" in system._state

    bucket = system._state["alice@example.com"]
    assert bucket.messages == []
    assert bucket.events == []
    assert bucket.contacts == []
    assert [f.id for f in bucket.folders] == ["inbox", "sent"]
    assert system.default_user == "alice@example.com"


def test_contact_model():
    """Test Contact model with all fields"""
    contact = Contact(
        id="test-id",
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        manager="manager-contact-id",
        position="Software Engineer",
    )
    assert contact.id == "test-id"
    assert contact.name == "John Doe"
    assert contact.email == "john@example.com"
    assert contact.phone == "555-1234"
    assert contact.manager == "manager-contact-id"
    assert contact.position == "Software Engineer"


def test_contact_model_optional_fields():
    """Test Contact model with only required fields"""
    contact = Contact(id="test-id", name="John Doe", email="john@example.com")
    assert contact.id == "test-id"
    assert contact.name == "John Doe"
    assert contact.email == "john@example.com"
    assert contact.phone is None
    assert contact.manager is None
    assert contact.position is None


def test_add_contact():
    """Test adding a contact with all fields"""
    system = EmailSystem()
    config = {"users": {"alice@example.com": {}}}
    system.initialize(config)

    # First create a manager contact
    manager_id = system.add_contact(name="Jane Smith", email="jane@example.com")

    contact_id = system.add_contact(
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        manager=manager_id,
        position="Software Engineer",
    )

    assert contact_id is not None
    assert len(system.effects) == 2  # manager + employee
    assert system.effects[1]["op"] == "add_contact"
    assert system.effects[1]["contact_id"] == contact_id


def test_add_contact_minimal():
    """Test adding a contact with minimal fields"""
    system = EmailSystem()
    config = {"users": {"alice@example.com": {}}}
    system.initialize(config)

    contact_id = system.add_contact(name="John Doe", email="john@example.com")

    assert contact_id is not None
    contacts = system.list_contacts()
    assert len(contacts) == 1
    contact = contacts[0]
    assert contact.name == "John Doe"
    assert contact.email == "john@example.com"
    assert contact.phone is None
    assert contact.manager is None
    assert contact.position is None


def test_list_contacts():
    """Test listing contacts"""
    system = EmailSystem()
    config = {"users": {"alice@example.com": {}}}
    system.initialize(config)

    # First create a manager contact
    manager_id = system.add_contact(name="Jane Smith", email="jane@example.com")

    # Add a contact
    contact_id = system.add_contact(
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        manager=manager_id,
        position="Software Engineer",
    )

    contacts = system.list_contacts()
    assert len(contacts) == 2  # manager + employee

    # Find the employee contact
    employee_contact = None
    for contact in contacts:
        if contact.id == contact_id:
            employee_contact = contact
            break

    assert employee_contact is not None
    assert employee_contact.id == contact_id
    assert employee_contact.name == "John Doe"
    assert employee_contact.email == "john@example.com"
    assert employee_contact.phone == "555-1234"
    assert employee_contact.manager == manager_id
    assert employee_contact.position == "Software Engineer"


def test_get_contact():
    """Test getting a specific contact by ID"""
    system = EmailSystem()
    config = {"users": {"alice@example.com": {}}}
    system.initialize(config)

    # First create a manager contact
    manager_id = system.add_contact(name="Jane Smith", email="jane@example.com")

    # Add a contact
    contact_id = system.add_contact(
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        manager=manager_id,
        position="Software Engineer",
    )

    # Get the contact
    contact = system.get_contact(contact_id)
    assert contact.id == contact_id
    assert contact.name == "John Doe"
    assert contact.email == "john@example.com"
    assert contact.phone == "555-1234"
    assert contact.manager == manager_id
    assert contact.position == "Software Engineer"

    # Check effects
    assert (
        len(system.effects) == 3
    )  # add_contact (manager) + add_contact (employee) + get_contact
    assert system.effects[2]["op"] == "get_contact"
    assert system.effects[2]["contact_id"] == contact_id


def test_get_contact_not_found():
    """Test getting a contact that doesn't exist"""
    system = EmailSystem()
    config = {"users": {"alice@example.com": {}}}
    system.initialize(config)

    with pytest.raises(EmailSystemError) as exc_info:
        system.get_contact("nonexistent-id")

    assert "Contact with id nonexistent-id not found" in str(exc_info.value)


def test_get_contact_with_different_user():
    """Test getting a contact for a specific user"""
    system = EmailSystem()
    config = {"users": {"alice@example.com": {}, "bob@example.com": {}}}
    system.initialize(config)

    # Add contact for Alice
    alice_contact_id = system.add_contact(
        name="Alice Contact",
        email="alice_contact@example.com",
        user="alice@example.com",
    )

    # Add contact for Bob
    bob_contact_id = system.add_contact(
        name="Bob Contact", email="bob_contact@example.com", user="bob@example.com"
    )

    # Get Alice's contact as Alice
    alice_contact = system.get_contact(alice_contact_id, user="alice@example.com")
    assert alice_contact.name == "Alice Contact"

    # Try to get Bob's contact as Alice (should fail)
    with pytest.raises(EmailSystemError):
        system.get_contact(bob_contact_id, user="alice@example.com")


def test_manager_contact_reference():
    """Test that manager field correctly references a contact ID"""
    system = EmailSystem()
    config = {"users": {"alice@example.com": {}}}
    system.initialize(config)

    # Create a manager contact
    manager_id = system.add_contact(
        name="Jane Smith", email="jane@example.com", position="Engineering Manager"
    )

    # Create an employee contact that references the manager
    employee_id = system.add_contact(
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        manager=manager_id,
        position="Software Engineer",
    )

    # Verify the employee's manager field contains the manager's contact ID
    employee = system.get_contact(employee_id)
    assert employee.manager == manager_id

    # Verify we can retrieve the manager using the ID from the employee
    manager = system.get_contact(employee.manager)
    assert manager.name == "Jane Smith"
    assert manager.position == "Engineering Manager"

    # Verify the manager has no manager (None)
    assert manager.manager is None


def test_organizational_hierarchy_manager_of_manager():
    """Test organizational hierarchy scenario: 5 contacts + 1 logged in user.
    Tests the query 'Email the manager of my manager the following testing'"""
    system = EmailSystem()

    # Set up logged in user
    logged_in_user = "john.employee@company.com"
    config = {"users": {logged_in_user: {}}}
    system.initialize(config)

    # 1. CEO - Top of the hierarchy
    ceo_id = system.add_contact(
        name="Sarah CEO",
        email="sarah.ceo@company.com",
        phone="555-0001",
        position="Chief Executive Officer",
        # No manager - top of hierarchy
    )

    # 2. VP - Reports to CEO
    vp_id = system.add_contact(
        name="Mike VP",
        email="mike.vp@company.com",
        phone="555-0002",
        manager=ceo_id,
        position="Vice President of Engineering",
    )

    # 3. Engineering Manager - Reports to VP
    manager_id = system.add_contact(
        name="Lisa Manager",
        email="lisa.manager@company.com",
        phone="555-0003",
        manager=vp_id,
        position="Engineering Manager",
    )

    # 4. Employee 1 (logged in user contact record) - Reports to Engineering Manager
    logged_in_user_contact_id = system.add_contact(
        name="John Employee",
        email=logged_in_user,
        phone="555-0004",
        manager=manager_id,
        position="Senior Software Engineer",
    )

    # 5. Employee 2 - Reports to Engineering Manager
    employee2_id = system.add_contact(
        name="Anna Employee",
        email="anna.employee@company.com",
        phone="555-0005",
        manager=manager_id,
        position="Software Engineer",
    )

    # 6. Employee 3 - Reports to Engineering Manager
    employee3_id = system.add_contact(
        name="David Employee",
        email="david.employee@company.com",
        phone="555-0006",
        manager=manager_id,
        position="Junior Software Engineer",
    )

    # Verify we have 6 contacts total
    all_contacts = system.list_contacts()
    assert len(all_contacts) == 6

    # Test the scenario: "Email the manager of my manager the following 'testing'"

    # Step 1: Find the logged-in user's contact
    logged_in_user_contact = system.get_contact(logged_in_user_contact_id)
    assert logged_in_user_contact.email == logged_in_user
    assert logged_in_user_contact.name == "John Employee"

    # Step 2: Find the logged-in user's manager
    my_manager_id = logged_in_user_contact.manager
    assert my_manager_id == manager_id
    my_manager = system.get_contact(my_manager_id)
    assert my_manager.name == "Lisa Manager"

    # Step 3: Find the manager's manager (manager of my manager)
    manager_of_manager_id = my_manager.manager
    assert manager_of_manager_id == vp_id
    manager_of_manager = system.get_contact(manager_of_manager_id)
    assert manager_of_manager.name == "Mike VP"
    assert manager_of_manager.email == "mike.vp@company.com"

    # Step 4: Send email to manager of my manager
    from thinkingbox_tools.toolslib.email_system import MessageCreate

    email_message = MessageCreate(
        to=manager_of_manager.email,
        cc=[],
        subject="Message from John Employee",
        body="testing",
    )

    message_id = system.send_message(email_message, user=logged_in_user)
    assert message_id is not None

    # Verify the email was sent
    # Count the effects: 6 add_contact + 3 get_contact + some list_contacts + 1 send_message
    send_effect = system.effects[-1]
    assert send_effect["op"] == "send_message"
    assert send_effect["user"] == logged_in_user
    assert send_effect["to"] == [manager_of_manager.email]
    assert send_effect["subject"] == "Message from John Employee"
    assert send_effect["body"] == "testing"

    # Additional verification: Test the organizational chain
    # CEO -> VP -> Manager -> Employee hierarchy

    # Verify CEO has no manager
    ceo = system.get_contact(ceo_id)
    assert ceo.manager is None
    assert ceo.position == "Chief Executive Officer"

    # Verify VP reports to CEO
    vp = system.get_contact(vp_id)
    assert vp.manager == ceo_id
    assert vp.position == "Vice President of Engineering"

    # Verify Manager reports to VP
    manager = system.get_contact(manager_id)
    assert manager.manager == vp_id
    assert manager.position == "Engineering Manager"

    # Verify all employees report to Manager
    employee1 = system.get_contact(logged_in_user_contact_id)
    employee2 = system.get_contact(employee2_id)
    employee3 = system.get_contact(employee3_id)

    assert employee1.manager == manager_id
    assert employee2.manager == manager_id
    assert employee3.manager == manager_id


def test_user_profile_functionality():
    """Test user profile functionality with initialization from YAML-like config"""
    system = EmailSystem()

    # Config that simulates loading from organizational_hierarchy.yaml
    config = {
        "users": {
            "alice@company.com": {
                "profile": {
                    "manager": "contact-001",
                    "phone": "34234-324234",
                    "email": "alice@company.com",
                    "position": "Data Scientist",
                },
                "contacts": [
                    {
                        "id": "contact-001",
                        "name": "Bob Manager",
                        "email": "bob@company.com",
                        "phone": "555-0101",
                        "manager": "contact-002",
                        "position": "Team Lead",
                    },
                    {
                        "id": "contact-002",
                        "name": "Carol VP",
                        "email": "carol@company.com",
                        "phone": "555-0102",
                        "manager": None,
                        "position": "Vice President",
                    },
                ],
            }
        }
    }

    system.initialize(config)

    # Test get_user_profile
    profile = system.get_user_profile("alice@company.com")
    assert profile.manager == "contact-001"
    assert profile.phone == "34234-324234"
    assert profile.email == "alice@company.com"
    assert profile.position == "Data Scientist"

    # Test get_user_manager
    manager = system.get_user_manager("alice@company.com")
    assert manager is not None
    assert manager.name == "Bob Manager"
    assert manager.email == "bob@company.com"
    assert manager.position == "Team Lead"
    assert manager.manager == "contact-002"

    # Test get_manager_of_manager
    manager_of_manager = system.get_manager_of_manager("alice@company.com")
    assert manager_of_manager is not None
    assert manager_of_manager.name == "Carol VP"
    assert manager_of_manager.email == "carol@company.com"
    assert manager_of_manager.position == "Vice President"
    assert manager_of_manager.manager is None

    # Test updating user profile
    from thinkingbox_tools.toolslib.email_system import UserProfile

    new_profile = UserProfile(
        manager="contact-002",  # Direct report to Carol VP now
        phone="555-9999",
        email="alice@company.com",
        position="Senior Data Scientist",
    )

    system.update_user_profile(new_profile, "alice@company.com")

    # Verify the update worked
    updated_profile = system.get_user_profile("alice@company.com")
    assert updated_profile.manager == "contact-002"
    assert updated_profile.phone == "555-9999"
    assert updated_profile.position == "Senior Data Scientist"

    # Now Alice's manager should be Carol VP directly
    new_manager = system.get_user_manager("alice@company.com")
    assert new_manager.name == "Carol VP"

    # And manager of manager should be None since Carol has no manager
    manager_of_manager_after_update = system.get_manager_of_manager("alice@company.com")
    assert manager_of_manager_after_update is None


def test_user_profile_edge_cases():
    """Test edge cases for user profile functionality"""
    system = EmailSystem()

    # Config with user that has no profile info
    config = {"users": {"bob@example.com": {}}}

    system.initialize(config)

    # Test getting profile for user with no profile data
    profile = system.get_user_profile("bob@example.com")
    assert profile.manager is None
    assert profile.phone is None
    assert profile.email is None
    assert profile.position is None

    # Test getting manager when user has no manager
    manager = system.get_user_manager("bob@example.com")
    assert manager is None

    # Test getting manager of manager when user has no manager
    manager_of_manager = system.get_manager_of_manager("bob@example.com")
    assert manager_of_manager is None

    # Test case where user has manager ID but contact doesn't exist
    from thinkingbox_tools.toolslib.email_system import UserProfile

    profile_with_invalid_manager = UserProfile(
        manager="nonexistent-contact-id", position="Test Position"
    )

    system.update_user_profile(profile_with_invalid_manager, "bob@example.com")

    # Should return None when manager contact doesn't exist
    manager = system.get_user_manager("bob@example.com")
    assert manager is None

    manager_of_manager = system.get_manager_of_manager("bob@example.com")
    assert manager_of_manager is None
