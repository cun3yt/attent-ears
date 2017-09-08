from django.contrib.postgres.fields import JSONField, HStoreField
from django.db import models
from core.mixins import TimeStampedMixin
from visualizer.models import User, Client

from stringcase import pascalcase


class SalesforceCustomFieldMapping(TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_custom_field_mapping'

    client = models.ForeignKey(Client)
    entity = models.CharField(max_length=50, db_index=True, blank=False, null=False)

    # Sample Data: "field1_mapped_to"=>"ARR", "field1_sfdc_name"=>"ARR__c"
    # Update Query: update salesforce_custom_field_mapping set
    #               "mapping" = 'field1_sfdc_name=>ARR__c,field1_mapped_to=>ARR'::hstore
    #               where id = 1;
    mapping = HStoreField()


class SalesforceEntityDescription(TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_entity_description'

    client = models.ForeignKey(Client, db_index=True)
    entity_name = models.TextField(db_index=True)
    standard_fields = JSONField()
    custom_fields = JSONField()

    def save_field_descriptions(self):
        pass


class SalesforceEntityMixin(models.Model):
    class Meta:
        abstract = True

    client = models.ForeignKey(Client)

    sfdc_id = models.TextField(db_index=True)
    is_deleted = models.TextField()
    rest_of_data = JSONField(default={})

    @classmethod
    def field_names(cls):
        return [f.name for f in cls._meta.fields]

    @classmethod
    def save_from_bulk_row(cls, row, client: Client):
        print('save_from_bulk_row is called')

        field_names = cls.field_names()
        overrides = cls.field_mapping_overrides()

        entity_dict = {}

        for field_name in field_names:
            row_index = pascalcase(field_name)
            try:
                row[row_index]
            except KeyError:
                continue
            dict_index = overrides[field_name] if (field_name in overrides) else field_name
            entity_dict[dict_index] = row[row_index]
            del row[row_index]

        entity_dict['rest_of_data'] = row
        entity_dict['client'] = client

        cls.objects.update_or_create(
            client=client,
            sfdc_id=entity_dict['sfdc_id'],
            defaults=entity_dict,
        )

    @classmethod
    def field_mapping_overrides(cls):
        """
        Override this method if needed for the subclasses to
        do field mapping overriding.

        It is a dictionary of
            * key: expected field name in the model
            * value: real field name in the model
        Example: key: "id", value: "sfdc_id" => { "id": "sfdc_id" }
        :return: dict
        """
        return {
            'id': 'sfdc_id',
        }


class SalesforceAccount(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_account'

    master_record_id = models.TextField()
    name = models.TextField()
    type = models.TextField()
    parent_id = models.TextField()
    billing_street = models.TextField()
    billing_city = models.TextField()
    billing_state = models.TextField()
    billing_postal_code = models.TextField()
    billing_country = models.TextField()
    billing_state_code = models.TextField()
    billing_country_code = models.TextField()
    billing_latitude = models.TextField()
    billing_longitude = models.TextField()
    billing_geocode_accuracy = models.TextField()
    shipping_street = models.TextField()
    shipping_city = models.TextField()
    shipping_state = models.TextField()
    shipping_postal_code = models.TextField()
    shipping_country = models.TextField()
    shipping_state_code = models.TextField()
    shipping_country_code = models.TextField()
    shipping_latitude = models.TextField()
    shipping_longitude = models.TextField()
    shipping_geocode_accuracy = models.TextField()
    phone = models.TextField()
    website = models.TextField()
    photo_url = models.TextField()
    industry = models.TextField()
    annual_revenue = models.TextField()
    number_of_employees = models.TextField()
    description = models.TextField()
    owner_id = models.TextField()
    created_date = models.TextField()
    created_by_id = models.TextField()
    last_modified_date = models.TextField()
    last_modified_by_id = models.TextField()
    system_modstamp = models.TextField()
    last_activity_date = models.TextField()
    last_viewed_date = models.TextField()
    last_referenced_date = models.TextField()
    jigsaw_company_id = models.TextField()
    account_source = models.TextField()


class SalesforceAccountHistory(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_account_history'

    account_id = models.TextField(db_index=True)
    created_by_id = models.TextField()
    created_date = models.TextField()
    field = models.TextField()
    old_value = models.TextField()
    new_value = models.TextField()


class SalesforceContact(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_contact'
    pass

    master_record_id = models.TextField()
    account_id = models.TextField(db_index=True)
    name = models.TextField()
    first_name = models.TextField()
    last_name = models.TextField()
    salutation = models.TextField()
    mailing_street = models.TextField()
    mailing_city = models.TextField()
    mailing_state = models.TextField()
    mailing_postal_code = models.TextField()
    mailing_country = models.TextField()
    mailing_state_code = models.TextField()
    mailing_country_code = models.TextField()
    mailing_latitude = models.TextField()
    mailing_longitude = models.TextField()
    mailing_geocode_accuracy = models.TextField()
    phone = models.TextField()
    fax = models.TextField()
    mobile_phone = models.TextField()
    email = models.TextField()
    title = models.TextField()
    department = models.TextField()
    lead_source = models.TextField()
    description = models.TextField()
    owner_id = models.TextField(db_index=True)
    has_opted_out_of_email = models.TextField()
    created_date = models.TextField()
    created_by_id = models.TextField()
    last_modified_date = models.TextField()
    last_modified_by_id = models.TextField()
    system_modstamp = models.TextField()
    last_activity_date = models.TextField()
    last_c_u_request_date = models.TextField()
    last_c_u_update_date = models.TextField()
    last_viewed_date = models.TextField()
    last_referenced_date = models.TextField()
    email_bounced_reason = models.TextField()
    email_bounced_date = models.TextField()
    is_email_bounced = models.TextField()
    photo_url = models.TextField()
    jigsaw_contact_id = models.TextField()


class SalesforceContactHistory(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_contact_history'
    pass

    contact_id = models.TextField(db_index=True)
    created_by_id = models.TextField(db_index=True)
    created_date = models.TextField()
    field = models.TextField()
    old_value = models.TextField()
    new_value = models.TextField()


class SalesforceOpportunity(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_opportunity'

    account_id = models.TextField(db_index=True)
    record_type_id = models.TextField()
    name = models.TextField()
    description = models.TextField()
    stage_name = models.TextField()
    amount = models.TextField()
    probability = models.TextField()
    close_date = models.TextField()
    type = models.TextField()
    next_step = models.TextField()
    lead_source = models.TextField()
    is_closed = models.TextField()
    is_won = models.TextField()
    forecast_category = models.TextField()
    forecast_category_name = models.TextField()
    campaign_id = models.TextField()
    has_opportunity_line_item = models.TextField()
    is_split = models.TextField()
    pricebook2_id = models.TextField()
    owner_id = models.TextField()
    created_date = models.TextField()
    created_by_id = models.TextField()
    last_modified_date = models.TextField()
    last_modified_by_id = models.TextField()
    system_modstamp = models.TextField()
    last_activity_date = models.TextField()
    fiscal_quarter = models.TextField()
    fiscal_year = models.TextField()
    fiscal = models.TextField()
    last_viewed_date = models.TextField()
    last_referenced_date = models.TextField()
    synced_quote_id = models.TextField()
    has_open_activity = models.TextField()
    has_overdue_task = models.TextField()


class SalesforceOpportunityHistory(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_opportunity_history'
    pass

    opportunity_id = models.TextField(db_index=True)
    created_by_id = models.TextField()
    created_date = models.TextField()
    stage_name = models.TextField()
    amount = models.TextField()
    expected_revenue = models.TextField()
    close_date = models.TextField()
    probability = models.TextField()
    forecast_category = models.TextField()
    system_modstamp = models.TextField()


class SalesforceOpportunityFieldHistory(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_opportunity_field_history'
    pass

    opportunity_id = models.TextField(db_index=True)
    created_by_id = models.TextField()
    created_date = models.TextField()
    field = models.TextField()
    old_value = models.TextField()
    new_value = models.TextField()


class SalesforceLead(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_lead'
    pass

    master_record_id = models.TextField()
    last_name = models.TextField()
    first_name = models.TextField()
    salutation = models.TextField()
    name = models.TextField()
    title = models.TextField()
    company = models.TextField()
    street = models.TextField()
    city = models.TextField()
    state = models.TextField()
    postal_code = models.TextField()
    country = models.TextField()
    state_code = models.TextField()
    country_code = models.TextField()
    latitude = models.TextField()
    longitude = models.TextField()
    geocode_accuracy = models.TextField()
    address = models.TextField()
    phone = models.TextField()
    mobile_phone = models.TextField()
    fax = models.TextField()
    email = models.TextField()
    website = models.TextField()
    photo_url = models.TextField()
    description = models.TextField()
    lead_source = models.TextField()
    status = models.TextField()
    industry = models.TextField()
    annual_revenue = models.TextField()
    number_of_employees = models.TextField()
    owner_id = models.TextField(db_index=True)
    has_opted_out_of_email = models.TextField()
    is_converted = models.TextField()
    converted_date = models.TextField()
    converted_account_id = models.TextField()
    converted_contact_id = models.TextField()
    converted_opportunity_id = models.TextField()
    is_unread_by_owner = models.TextField()
    created_date = models.TextField()
    created_by_id = models.TextField()
    last_modified_date = models.TextField()
    last_modified_by_id = models.TextField()
    system_modstamp = models.TextField()
    last_activity_date = models.TextField()
    last_viewed_date = models.TextField()
    last_referenced_date = models.TextField()
    jigsaw_contact_id = models.TextField()
    email_bounced_reason = models.TextField()
    email_bounced_date = models.TextField()


class SalesforceTask(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_task'
    pass

    who_id = models.TextField(db_index=True)
    what_id = models.TextField(db_index=True)
    who_count = models.TextField()
    what_count = models.TextField()
    subject = models.TextField()
    activity_date = models.TextField()
    status = models.TextField()
    priority = models.TextField()
    is_high_priority = models.TextField()
    owner_id = models.TextField(db_index=True)
    description = models.TextField()
    type = models.TextField()
    account_id = models.TextField(db_index=True)
    is_closed = models.TextField()
    created_date = models.TextField()
    created_by_id = models.TextField()
    last_modified_date = models.TextField()
    last_modified_by_id = models.TextField()
    system_modstamp = models.TextField()
    is_archived = models.TextField()
    call_duration_in_seconds = models.TextField()
    call_type = models.TextField()
    call_disposition = models.TextField()
    call_object = models.TextField()
    reminder_date_time = models.TextField()
    is_reminder_set = models.TextField()
    recurrence_activity_id = models.TextField()
    is_recurrence = models.TextField()
    recurrence_start_date_only = models.TextField()
    recurrence_end_date_only = models.TextField()
    recurrence_time_zone_sid_key = models.TextField()
    recurrence_type = models.TextField()
    recurrence_interval = models.TextField()
    recurrence_day_of_week_mask = models.TextField()
    recurrence_day_of_month = models.TextField()
    recurrence_instance = models.TextField()
    recurrence_month_of_year = models.TextField()
    recurrence_regenerated_type = models.TextField()
    task_subtype = models.TextField()


class SalesforceUser(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_user'
    pass

    username = models.TextField()
    last_name = models.TextField()
    first_name = models.TextField()
    name = models.TextField()
    company_name = models.TextField()
    division = models.TextField()
    department = models.TextField()
    title = models.TextField()
    street = models.TextField()
    city = models.TextField()
    state = models.TextField()
    postal_code = models.TextField()
    country = models.TextField()
    state_code = models.TextField()
    country_code = models.TextField()
    latitude = models.TextField()
    longitude = models.TextField()
    geocode_accuracy = models.TextField()
    address = models.TextField()
    email = models.TextField()
    email_preferences_auto_bcc = models.TextField()
    email_preferences_auto_bcc_stay_in_touch = models.TextField()
    email_preferences_stay_in_touch_reminder = models.TextField()
    sender_email = models.TextField()
    sender_name = models.TextField()
    signature = models.TextField()
    stay_in_touch_subject = models.TextField()
    stay_in_touch_signature = models.TextField()
    stay_in_touch_note = models.TextField()
    phone = models.TextField()
    fax = models.TextField()
    mobile_phone = models.TextField()
    alias = models.TextField()
    community_nickname = models.TextField()
    badge_text = models.TextField()
    is_active = models.TextField()
    time_zone_sid_key = models.TextField()
    user_role_id = models.TextField()
    locale_sid_key = models.TextField()
    receives_info_emails = models.TextField()
    receives_admin_info_emails = models.TextField()
    email_encoding_key = models.TextField()
    profile_id = models.TextField()
    user_type = models.TextField()
    language_locale_key = models.TextField()
    employee_number = models.TextField()
    delegated_approver_id = models.TextField()
    manager_id = models.TextField()
    last_login_date = models.TextField()
    last_password_change_date = models.TextField()
    created_date = models.TextField()
    created_by_id = models.TextField()
    last_modified_date = models.TextField()
    last_modified_by_id = models.TextField()
    system_modstamp = models.TextField()
    offline_trial_expiration_date = models.TextField()
    offline_pda_trial_expiration_date = models.TextField()
    user_permissions_marketing_user = models.TextField()
    user_permissions_offline_user = models.TextField()
    user_permissions_avantgo_user = models.TextField()
    user_permissions_call_center_auto_login = models.TextField()
    user_permissions_mobile_user = models.TextField()
    user_permissions_s_f_content_user = models.TextField()
    user_permissions_interaction_user = models.TextField()
    user_permissions_support_user = models.TextField()
    user_permissions_chatter_answers_user = models.TextField()
    forecast_enabled = models.TextField()
    user_preferences_activity_reminders_popup = models.TextField()
    user_preferences_event_reminders_checkbox_default = models.TextField()
    user_preferences_task_reminders_checkbox_default = models.TextField()
    user_preferences_reminder_sound_off = models.TextField()
    user_preferences_disable_all_feeds_email = models.TextField()
    user_preferences_disable_followers_email = models.TextField()
    user_preferences_disable_profile_post_email = models.TextField()
    user_preferences_disable_change_comment_email = models.TextField()
    user_preferences_disable_later_comment_email = models.TextField()
    user_preferences_dis_prof_post_comment_email = models.TextField()
    user_preferences_apex_pages_developer_mode = models.TextField()
    user_preferences_hide_c_s_n_get_chatter_mobile_task = models.TextField()
    user_preferences_disable_mentions_post_email = models.TextField()
    user_preferences_dis_mentions_comment_email = models.TextField()
    user_preferences_hide_c_s_n_desktop_task = models.TextField()
    user_preferences_hide_chatter_onboarding_splash = models.TextField()
    user_preferences_hide_second_chatter_onboarding_splash = models.TextField()
    user_preferences_dis_comment_after_like_email = models.TextField()
    user_preferences_disable_like_email = models.TextField()
    user_preferences_sort_feed_by_comment = models.TextField()
    user_preferences_disable_message_email = models.TextField()
    user_preferences_disable_bookmark_email = models.TextField()
    user_preferences_disable_share_post_email = models.TextField()
    user_preferences_enable_auto_sub_for_feeds = models.TextField()
    user_preferences_disable_file_share_notifications_for_api = models.TextField()
    user_preferences_show_title_to_external_users = models.TextField()
    user_preferences_show_manager_to_external_users = models.TextField()
    user_preferences_show_email_to_external_users = models.TextField()
    user_preferences_show_work_phone_to_external_users = models.TextField()
    user_preferences_show_mobile_phone_to_external_users = models.TextField()
    user_preferences_show_fax_to_external_users = models.TextField()
    user_preferences_show_street_address_to_external_users = models.TextField()
    user_preferences_show_city_to_external_users = models.TextField()
    user_preferences_show_state_to_external_users = models.TextField()
    user_preferences_show_postal_code_to_external_users = models.TextField()
    user_preferences_show_country_to_external_users = models.TextField()
    user_preferences_show_profile_pic_to_guest_users = models.TextField()
    user_preferences_show_title_to_guest_users = models.TextField()
    user_preferences_show_city_to_guest_users = models.TextField()
    user_preferences_show_state_to_guest_users = models.TextField()
    user_preferences_show_postal_code_to_guest_users = models.TextField()
    user_preferences_show_country_to_guest_users = models.TextField()
    user_preferences_hide_s1_browser_u_i = models.TextField()
    user_preferences_disable_endorsement_email = models.TextField()
    user_preferences_path_assistant_collapsed = models.TextField()
    user_preferences_cache_diagnostics = models.TextField()
    user_preferences_show_email_to_guest_users = models.TextField()
    user_preferences_show_manager_to_guest_users = models.TextField()
    user_preferences_show_work_phone_to_guest_users = models.TextField()
    user_preferences_show_mobile_phone_to_guest_users = models.TextField()
    user_preferences_show_fax_to_guest_users = models.TextField()
    user_preferences_show_street_address_to_guest_users = models.TextField()
    user_preferences_lightning_experience_preferred = models.TextField()
    user_preferences_preview_lightning = models.TextField()
    user_preferences_hide_end_user_onboarding_assistant_modal = models.TextField()
    user_preferences_hide_lightning_migration_modal = models.TextField()
    user_preferences_hide_sfx_welcome_mat = models.TextField()
    user_preferences_hide_bigger_photo_callout = models.TextField()
    user_preferences_global_nav_bar_w_t_shown = models.TextField()
    user_preferences_global_nav_grid_menu_w_t_shown = models.TextField()
    user_preferences_create_l_e_x_apps_w_t_shown = models.TextField()
    user_preferences_favorites_w_t_shown = models.TextField()
    user_preferences_record_home_section_collapse_w_t_shown = models.TextField()
    user_preferences_record_home_reserved_w_t_shown = models.TextField()
    user_preferences_favorites_show_top_favorites = models.TextField()
    contact_id = models.TextField(db_index=True)
    account_id = models.TextField(db_index=True)
    call_center_id = models.TextField()
    extension = models.TextField()
    federation_identifier = models.TextField()
    about_me = models.TextField()
    full_photo_url = models.TextField()
    small_photo_url = models.TextField()
    is_ext_indicator_visible = models.TextField()
    medium_photo_url = models.TextField()
    digest_frequency = models.TextField()
    default_group_notification_frequency = models.TextField()
    last_viewed_date = models.TextField()
    last_referenced_date = models.TextField()
    banner_photo_url = models.TextField()
    small_banner_photo_url = models.TextField()
    medium_banner_photo_url = models.TextField()
    is_profile_photo_active = models.TextField()


class SalesforceUserRole(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_user_role'
    pass

    name = models.TextField()
    parent_role_id = models.TextField()
    rollup_description = models.TextField()
    opportunity_access_for_account_owner = models.TextField()
    case_access_for_account_owner = models.TextField()
    contact_access_for_account_owner = models.TextField()
    forecast_user_id = models.TextField()
    may_forecast_manager_share = models.TextField()
    last_modified_date = models.TextField()
    last_modified_by_id = models.TextField()
    system_modstamp = models.TextField()
    developer_name = models.TextField()
    portal_account_id = models.TextField()
    portal_type = models.TextField()
    portal_account_owner_id = models.TextField()


class SalesforceEvent(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_event'
    pass

    who_id = models.TextField(db_index=True)
    what_id = models.TextField(db_index=True)
    who_count = models.TextField()
    what_count = models.TextField()
    subject = models.TextField()
    is_all_day_event = models.TextField()
    activity_date_time = models.TextField()
    activity_date = models.TextField()
    duration_in_minutes = models.TextField()
    start_date_time = models.TextField()
    end_date_time = models.TextField()
    description = models.TextField()
    account_id = models.TextField(db_index=True)
    owner_id = models.TextField(db_index=True)
    type = models.TextField()
    is_private = models.TextField()
    show_as = models.TextField()
    is_child = models.TextField()
    is_group_event = models.TextField()
    group_event_type = models.TextField()
    created_date = models.TextField()
    created_by_id = models.TextField()
    last_modified_date = models.TextField()
    last_modified_by_id = models.TextField()
    system_modstamp = models.TextField()
    is_archived = models.TextField()
    recurrence_activity_id = models.TextField()
    is_recurrence = models.TextField()
    recurrence_start_date_time = models.TextField()
    recurrence_end_date_only = models.TextField()
    recurrence_time_zone_sid_key = models.TextField()
    recurrence_type = models.TextField()
    recurrence_interval = models.TextField()
    recurrence_day_of_week_mask = models.TextField()
    recurrence_day_of_month = models.TextField()
    recurrence_instance = models.TextField()
    recurrence_month_of_year = models.TextField()
    reminder_date_time = models.TextField()
    is_reminder_set = models.TextField()
    event_subtype = models.TextField()
