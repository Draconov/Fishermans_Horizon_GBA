from __future__ import annotations

from dataclasses import dataclass
import struct


@dataclass(frozen=True)
class DexField:
    class_descriptor: str
    name: str
    type_descriptor: str


@dataclass(frozen=True)
class DexMethod:
    class_descriptor: str
    name: str
    prototype: str


@dataclass(frozen=True)
class DexEncodedMethod:
    method_index: int
    method: DexMethod
    access_flags: int
    code_offset: int


@dataclass(frozen=True)
class DexCodeItem:
    code_offset: int
    registers_size: int
    ins_size: int
    outs_size: int
    tries_size: int
    debug_info_offset: int
    code_units: tuple[int, ...]


class DexFile:
    def __init__(self, data: bytes):
        if len(data) < 112 or not data.startswith(b"dex\n"):
            raise ValueError("invalid DEX magic or truncated header")
        self._data = data
        self.file_size = self._u32(32)
        self.header_size = self._u32(36)
        if self.header_size < 112 or self.file_size > len(data):
            raise ValueError("invalid DEX header")

        self.string_ids_size = self._u32(56)
        self.string_ids_off = self._u32(60)
        self.type_ids_size = self._u32(64)
        self.type_ids_off = self._u32(68)
        self.proto_ids_size = self._u32(72)
        self.proto_ids_off = self._u32(76)
        self.field_ids_size = self._u32(80)
        self.field_ids_off = self._u32(84)
        self.method_ids_size = self._u32(88)
        self.method_ids_off = self._u32(92)
        self.class_defs_size = self._u32(96)
        self.class_defs_off = self._u32(100)

        self._strings: tuple[str, ...] | None = None
        self._types: tuple[str, ...] | None = None
        self._fields: tuple[DexField, ...] | None = None
        self._methods: tuple[DexMethod, ...] | None = None
        self._encoded_methods: tuple[DexEncodedMethod, ...] | None = None
        self._classes: tuple[str, ...] | None = None

    def _u16(self, offset: int) -> int:
        limit = getattr(self, "file_size", len(self._data))
        if offset < 0 or offset + 2 > limit:
            raise ValueError("DEX read outside file")
        return struct.unpack_from("<H", self._data, offset)[0]

    def _u32(self, offset: int) -> int:
        limit = getattr(self, "file_size", len(self._data))
        if offset < 0 or offset + 4 > limit:
            raise ValueError("DEX read outside file")
        return struct.unpack_from("<I", self._data, offset)[0]

    def _uleb128(self, offset: int) -> tuple[int, int]:
        value = 0
        shift = 0
        cursor = offset
        for _ in range(5):
            if cursor >= self.file_size:
                raise ValueError("truncated ULEB128 value")
            byte = self._data[cursor]
            cursor += 1
            value |= (byte & 0x7F) << shift
            if byte & 0x80 == 0:
                return value, cursor
            shift += 7
        raise ValueError("invalid ULEB128 value")

    @staticmethod
    def _decode_mutf8(raw: bytes) -> str:
        # The reference game's symbol surface is ASCII/UTF-8 compatible. DEX
        # uses MUTF-8, whose only incompatibility relevant here is encoded NUL;
        # normalize that form before decoding and preserve unknown bytes.
        raw = raw.replace(b"\xC0\x80", b"\x00")
        return raw.decode("utf-8", errors="replace")

    def strings(self) -> tuple[str, ...]:
        if self._strings is None:
            values: list[str] = []
            for index in range(self.string_ids_size):
                item_off = self._u32(self.string_ids_off + index * 4)
                _, cursor = self._uleb128(item_off)
                end = self._data.find(b"\x00", cursor, self.file_size)
                if end < 0:
                    raise ValueError("unterminated DEX string")
                values.append(self._decode_mutf8(self._data[cursor:end]))
            self._strings = tuple(values)
        return self._strings

    def _type_descriptors(self) -> tuple[str, ...]:
        if self._types is None:
            strings = self.strings()
            values = []
            for index in range(self.type_ids_size):
                descriptor_idx = self._u32(self.type_ids_off + index * 4)
                values.append(strings[descriptor_idx])
            self._types = tuple(values)
        return self._types

    def class_descriptors(self) -> tuple[str, ...]:
        if self._classes is None:
            types = self._type_descriptors()
            values = []
            for index in range(self.class_defs_size):
                class_idx = self._u32(self.class_defs_off + index * 32)
                values.append(types[class_idx])
            self._classes = tuple(values)
        return self._classes

    def fields(self) -> tuple[DexField, ...]:
        if self._fields is None:
            strings = self.strings()
            types = self._type_descriptors()
            values: list[DexField] = []
            for index in range(self.field_ids_size):
                field_off = self.field_ids_off + index * 8
                class_idx = self._u16(field_off)
                type_idx = self._u16(field_off + 2)
                name_idx = self._u32(field_off + 4)
                values.append(
                    DexField(
                        class_descriptor=types[class_idx],
                        name=strings[name_idx],
                        type_descriptor=types[type_idx],
                    )
                )
            self._fields = tuple(values)
        return self._fields

    def _prototype(self, proto_idx: int) -> str:
        types = self._type_descriptors()
        proto_off = self.proto_ids_off + proto_idx * 12
        return_type_idx = self._u32(proto_off + 4)
        parameters_off = self._u32(proto_off + 8)

        parameters: list[str] = []
        if parameters_off:
            size = self._u32(parameters_off)
            for index in range(size):
                type_idx = self._u16(parameters_off + 4 + index * 2)
                parameters.append(types[type_idx])

        return f"({''.join(parameters)}){types[return_type_idx]}"

    def methods(self) -> tuple[DexMethod, ...]:
        if self._methods is None:
            strings = self.strings()
            types = self._type_descriptors()
            values: list[DexMethod] = []
            for index in range(self.method_ids_size):
                method_off = self.method_ids_off + index * 8
                class_idx = self._u16(method_off)
                proto_idx = self._u16(method_off + 2)
                name_idx = self._u32(method_off + 4)
                values.append(
                    DexMethod(
                        class_descriptor=types[class_idx],
                        name=strings[name_idx],
                        prototype=self._prototype(proto_idx),
                    )
                )
            self._methods = tuple(values)
        return self._methods

    def encoded_methods(self) -> tuple[DexEncodedMethod, ...]:
        if self._encoded_methods is None:
            methods = self.methods()
            values: list[DexEncodedMethod] = []

            for class_index in range(self.class_defs_size):
                class_def_off = self.class_defs_off + class_index * 32
                class_data_off = self._u32(class_def_off + 24)
                if not class_data_off:
                    continue

                cursor = class_data_off
                static_fields_size, cursor = self._uleb128(cursor)
                instance_fields_size, cursor = self._uleb128(cursor)
                direct_methods_size, cursor = self._uleb128(cursor)
                virtual_methods_size, cursor = self._uleb128(cursor)

                for field_count in (static_fields_size, instance_fields_size):
                    field_index = 0
                    for _ in range(field_count):
                        index_diff, cursor = self._uleb128(cursor)
                        _access_flags, cursor = self._uleb128(cursor)
                        field_index += index_diff
                        if field_index >= self.field_ids_size:
                            raise ValueError("encoded field index outside field table")

                for method_count in (direct_methods_size, virtual_methods_size):
                    method_index = 0
                    for _ in range(method_count):
                        index_diff, cursor = self._uleb128(cursor)
                        access_flags, cursor = self._uleb128(cursor)
                        code_offset, cursor = self._uleb128(cursor)
                        method_index += index_diff
                        if method_index >= len(methods):
                            raise ValueError("encoded method index outside method table")
                        values.append(
                            DexEncodedMethod(
                                method_index=method_index,
                                method=methods[method_index],
                                access_flags=access_flags,
                                code_offset=code_offset,
                            )
                        )

            self._encoded_methods = tuple(values)
        return self._encoded_methods

    def _code_item(self, code_offset: int) -> DexCodeItem:
        if code_offset <= 0 or code_offset + 16 > self.file_size:
            raise ValueError("invalid DEX code item offset")

        registers_size = self._u16(code_offset)
        ins_size = self._u16(code_offset + 2)
        outs_size = self._u16(code_offset + 4)
        tries_size = self._u16(code_offset + 6)
        debug_info_offset = self._u32(code_offset + 8)
        insns_size = self._u32(code_offset + 12)
        insns_offset = code_offset + 16
        insns_bytes = insns_size * 2
        if insns_offset + insns_bytes > self.file_size:
            raise ValueError("truncated DEX code item")
        code_units = struct.unpack_from(f"<{insns_size}H", self._data, insns_offset)
        return DexCodeItem(
            code_offset=code_offset,
            registers_size=registers_size,
            ins_size=ins_size,
            outs_size=outs_size,
            tries_size=tries_size,
            debug_info_offset=debug_info_offset,
            code_units=tuple(code_units),
        )


    def _class_def_offset(self, class_descriptor: str) -> int:
        types = self._type_descriptors()
        for index in range(self.class_defs_size):
            class_def_off = self.class_defs_off + index * 32
            class_idx = self._u32(class_def_off)
            if types[class_idx] == class_descriptor:
                return class_def_off
        raise KeyError(f"class not found: {class_descriptor}")

    def _static_field_indexes(self, class_def_off: int) -> tuple[int, ...]:
        class_data_off = self._u32(class_def_off + 24)
        if not class_data_off:
            return ()

        cursor = class_data_off
        static_fields_size, cursor = self._uleb128(cursor)
        instance_fields_size, cursor = self._uleb128(cursor)
        _direct_methods_size, cursor = self._uleb128(cursor)
        _virtual_methods_size, cursor = self._uleb128(cursor)

        indexes: list[int] = []
        field_index = 0
        for _ in range(static_fields_size):
            index_diff, cursor = self._uleb128(cursor)
            _access_flags, cursor = self._uleb128(cursor)
            field_index += index_diff
            if field_index >= self.field_ids_size:
                raise ValueError("encoded static field index outside field table")
            indexes.append(field_index)

        field_index = 0
        for _ in range(instance_fields_size):
            index_diff, cursor = self._uleb128(cursor)
            _access_flags, cursor = self._uleb128(cursor)
            field_index += index_diff
            if field_index >= self.field_ids_size:
                raise ValueError("encoded instance field index outside field table")

        return tuple(indexes)

    def _encoded_value(self, offset: int) -> tuple[object, int]:
        if offset >= self.file_size:
            raise ValueError("truncated DEX encoded value")
        header = self._data[offset]
        offset += 1
        value_type = header & 0x1F
        value_arg = header >> 5
        size = value_arg + 1

        if value_type == 0x1E:  # VALUE_NULL
            return None, offset
        if value_type == 0x1F:  # VALUE_BOOLEAN
            if value_arg > 1:
                raise ValueError("invalid DEX boolean encoded value")
            return bool(value_arg), offset
        if offset + size > self.file_size:
            raise ValueError("truncated DEX encoded value payload")

        raw = self._data[offset:offset + size]
        offset += size
        unsigned_value = int.from_bytes(raw, "little", signed=False)

        if value_type in (0x00, 0x02, 0x04, 0x06):  # byte/short/int/long
            bit_count = size * 8
            sign_bit = 1 << (bit_count - 1)
            if unsigned_value & sign_bit:
                unsigned_value -= 1 << bit_count
            return unsigned_value, offset
        if value_type == 0x03:  # char
            return unsigned_value, offset
        if value_type == 0x17:  # string index
            strings = self.strings()
            if unsigned_value >= len(strings):
                raise ValueError("encoded string index outside string table")
            return strings[unsigned_value], offset

        raise ValueError(f"unsupported DEX encoded value type: {value_type:#x}")

    def static_field_values(self, class_descriptor: str) -> dict[str, object]:
        class_def_off = self._class_def_offset(class_descriptor)
        static_values_off = self._u32(class_def_off + 28)
        if not static_values_off:
            return {}

        field_indexes = self._static_field_indexes(class_def_off)
        value_count, cursor = self._uleb128(static_values_off)
        if value_count > len(field_indexes):
            raise ValueError("more static values than static fields")

        fields = self.fields()
        result: dict[str, object] = {}
        for field_index in field_indexes[:value_count]:
            value, cursor = self._encoded_value(cursor)
            result[fields[field_index].name] = value
        return result

    def method_code(
        self,
        class_descriptor: str,
        name: str,
        prototype: str | None = None,
    ) -> DexCodeItem:
        matches = [
            method
            for method in self.encoded_methods()
            if method.method.class_descriptor == class_descriptor
            and method.method.name == name
            and (prototype is None or method.method.prototype == prototype)
        ]
        if not matches:
            raise KeyError(f"method not found: {class_descriptor}->{name}")
        if len(matches) != 1:
            raise KeyError(
                f"ambiguous method: {class_descriptor}->{name}; specify prototype"
            )
        code_offset = matches[0].code_offset
        if not code_offset:
            raise KeyError(f"method has no code: {class_descriptor}->{name}")
        return self._code_item(code_offset)
